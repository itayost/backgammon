import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QKeyEvent
    from PyQt6.QtCore import QEvent
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, 'PyQt6 is not installed')
class AppWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        from ui import theme
        from ui.fonts import load_fonts
        cls.families = load_fonts()
        cls.app.setStyleSheet(theme.stylesheet())

    def setUp(self):
        from ui.app_window import AppWindow
        self.window = AppWindow()
        self.window.show()

    def tearDown(self):
        self.window.close()

    def test_fonts_are_bundled(self):
        from ui import theme
        self.assertTrue(set(theme.FAMILIES.values()) <= self.families)

    def test_starts_on_home(self):
        self.assertEqual(self.window.navigator.current(), 'home')

    def test_how_to_and_back(self):
        self.window.home.how_to_button.click()
        self.assertEqual(self.window.navigator.current(), 'how_to')
        self.window.how_to.back_button.click()
        self.assertEqual(self.window.navigator.current(), 'home')

    def test_escape_goes_back(self):
        self.window.navigator.go('how_to')
        self.app.sendEvent(self.window.how_to, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape,
                                                         Qt.KeyboardModifier.NoModifier))
        self.assertEqual(self.window.navigator.current(), 'home')

    def test_game_starts_and_leaves_cleanly(self):
        self.window.start_game({1: 'medium', -1: 'easy'}, step_delay_ms=0)
        self.assertEqual(self.window.navigator.current(), 'game')
        screen = self.window.navigator.screens['game']
        self.window.leave_game()
        self.assertEqual(self.window.navigator.current(), 'home')
        self.assertNotIn('game', self.window.navigator.screens)
        self.assertEqual(screen.session.listeners, [])


class GameScreenTest(unittest.TestCase):
    """Clicks on the board and the turn buttons, two players on one computer"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from ui.screens.game import GameScreen
        self.screen = GameScreen({})
        self.session = self.screen.session
        self.session.start(opening=(5, 3))

    def tearDown(self):
        self.screen.shutdown()

    def test_select_then_move(self):
        self.screen.on_board_click('point', 17)
        self.assertEqual(self.screen.selected, 17)
        self.assertEqual(self.screen.board.view.targets, {20, 22})
        self.screen.on_board_click('point', 22)
        self.assertEqual(self.session.board[22], [1, 1])
        self.assertIsNone(self.screen.selected)
        self.assertEqual(self.session.dice_left, [3])

    def test_click_selected_again_cancels(self):
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 17)
        self.assertIsNone(self.screen.selected)

    def test_click_another_source_switches(self):
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 12)
        self.assertEqual(self.screen.selected, 12)

    def test_buttons_follow_the_turn(self):
        self.assertFalse(self.screen.roll_button.isVisibleTo(self.screen))
        self.assertFalse(self.screen.undo_button.isEnabled())
        self.assertFalse(self.screen.done_button.isEnabled())
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 22)
        self.assertTrue(self.screen.undo_button.isEnabled())
        self.screen.on_board_click('point', 19)
        self.screen.on_board_click('point', 22)
        self.assertTrue(self.screen.done_button.isEnabled())
        self.screen.undo_button.click()
        self.assertFalse(self.screen.done_button.isEnabled())
        self.screen.on_board_click('point', 19)
        self.screen.on_board_click('point', 22)
        self.screen.done_button.click()
        self.assertEqual(self.session.player, -1)
        self.assertTrue(self.screen.roll_button.isVisibleTo(self.screen))
        self.screen.roll_button.click()
        self.assertFalse(self.screen.roll_button.isVisibleTo(self.screen))

    def test_bear_off_through_the_tray(self):
        board = [[0, 0] for _ in range(26)]
        board[0], board[25] = [0, 1], [0, -1]
        board[22] = [2, 1]
        board[3] = [2, -1]
        self.session.board = board
        self.session.player = 1
        from game.session import Phase
        self.session.phase = Phase.AWAIT_ROLL
        self.session.roll([6, 2])
        self.screen.on_board_click('point', 22)
        self.assertTrue(self.screen.board.view.tray_target)
        self.screen.on_board_click('tray', None)
        self.assertEqual(self.session.board[22], [1, 1])
        self.assertEqual(self.session.dice_left, [2])

    def test_computer_turn_ignores_clicks(self):
        from ui.screens.game import GameScreen
        screen = GameScreen({1: 'easy'}, step_delay_ms=0)
        screen.session.start(opening=(5, 3))
        screen.on_board_click('point', 17)
        self.assertIsNone(screen.selected)
        self.assertEqual(screen.board.view.sources, set())
        screen.shutdown()


if __name__ == '__main__':
    unittest.main()
