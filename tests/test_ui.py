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
        self.window.start_game({1: 'medium', -1: 'easy'})
        self.assertEqual(self.window.navigator.current(), 'game')
        screen = self.window.navigator.screens['game']
        self.window.leave_game()
        self.assertEqual(self.window.navigator.current(), 'home')
        self.assertNotIn('game', self.window.navigator.screens)
        self.assertEqual(screen.model.list_of_controllers, [])

    def test_declining_another_game_returns_home(self):
        self.window.start_game({})
        board = self.window.navigator.screens['game'].board
        board.on_quit()
        self.assertEqual(self.window.navigator.current(), 'home')


if __name__ == '__main__':
    unittest.main()
