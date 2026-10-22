import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication = None

if QApplication is not None:
    from ai.ai_controller import AIController
    from ai.player import ComputerPlayer
    from game.session import GameSession, Phase


@unittest.skipIf(QApplication is None, 'PyQt6 is not installed')
class AIControllerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def run_until(self, condition, timeout_ms=60000):
        loop = QEventLoop()
        check = QTimer()
        check.timeout.connect(lambda: condition() and loop.quit())
        check.start(5)
        QTimer.singleShot(timeout_ms, loop.quit)
        loop.exec()
        check.stop()

    def computers(self):
        return {1: ComputerPlayer('medium', rng=random.Random(1)), -1: ComputerPlayer('easy', rng=random.Random(2))}

    def test_computers_play_a_full_game(self):
        session = GameSession(random.Random(5))
        ai = AIController(session, self.computers(), step_delay_ms=0, roll_delay_ms=0)
        session.start()
        self.run_until(lambda: session.phase == Phase.GAME_OVER)
        ai.stop()
        self.assertEqual(session.phase, Phase.GAME_OVER)
        winner = session.stats.winner
        self.assertEqual(sum(count for count, owner in session.board if owner == winner), 0)
        self.assertGreater(session.stats.turns, 10)

    def test_human_turn_is_left_alone(self):
        session = GameSession(random.Random(5))
        ai = AIController(session, {-1: ComputerPlayer('easy')}, step_delay_ms=0, roll_delay_ms=0)
        session.start(opening=(6, 1))
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        self.assertEqual(session.player, 1)
        self.assertEqual(session.phase, Phase.MOVING)
        ai.stop()

    def test_pause_holds_and_resume_continues(self):
        session = GameSession(random.Random(5))
        ai = AIController(session, {1: ComputerPlayer('easy')}, step_delay_ms=0, roll_delay_ms=0)
        ai.pause()
        session.start(opening=(6, 1))
        loop = QEventLoop()
        QTimer.singleShot(300, loop.quit)
        loop.exec()
        self.assertEqual(session.dice_left, [6, 1])
        ai.resume()
        self.run_until(lambda: session.player == -1)
        self.assertEqual(session.player, -1)
        ai.stop()

    def test_result_of_an_old_turn_is_ignored(self):
        session = GameSession(random.Random(5))
        ai = AIController(session, {}, step_delay_ms=0)
        session.start(opening=(6, 1))
        old = ai.generation
        session.start(opening=(6, 1))
        ai.on_thought(old, [session.legal[0]])
        self.assertEqual(ai.steps, [])
        ai.stop()


if __name__ == '__main__':
    unittest.main()
