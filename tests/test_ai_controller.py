import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PyQt6.QtCore import QEventLoop, QTimer
    from PyQt6.QtWidgets import QApplication
except ImportError:  # the rules tests run without Qt
    QApplication = None

if QApplication is not None:
    from ai.ai_controller import AIController
    from ai.player import ComputerPlayer
    from backgammon import backgammon


class Recorder:
    def __init__(self):
        self.winners = []

    def to_gui_winner(self, player):
        self.winners.append(player)

    def __getattr__(self, name):
        return lambda *args: None


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

    def test_computer_plays_a_full_game(self):
        model = backgammon()
        recorder = Recorder()
        model.list_of_controllers.append(recorder)
        computers = {1: ComputerPlayer('medium', rng=random.Random(1)),
                     -1: ComputerPlayer('easy', rng=random.Random(2))}
        ai = AIController(model, computers, step_delay_ms=0)
        self.run_until(lambda: recorder.winners)
        ai.wait_for_threads()
        self.assertEqual(len(recorder.winners), 1)
        self.assertEqual(sum(cell[0] for cell in model.board if cell[1] == recorder.winners[0]), 0)

    def test_result_of_an_old_turn_is_ignored(self):
        model = backgammon()
        ai = AIController(model, {}, step_delay_ms=0)
        old = ai.generation
        ai.to_gui_new_game(model.board)
        ai.on_thought(old, [model.moves[0]])
        self.assertFalse(ai.timer.isActive())
        self.assertEqual(ai.steps, [])


if __name__ == '__main__':
    unittest.main()
