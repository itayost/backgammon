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


def make_window():
    """An app window with settings and statistics in a temporary folder"""
    import tempfile
    from PyQt6.QtCore import QSettings
    from stores.settings_store import SettingsStore
    from stores.stats_store import StatsStore
    from ui.app_window import AppWindow
    folder = tempfile.TemporaryDirectory()
    settings = SettingsStore(QSettings(os.path.join(folder.name, 'settings.ini'), QSettings.Format.IniFormat))
    stats = StatsStore(os.path.join(folder.name, 'stats.json'))
    return AppWindow(settings, stats), folder


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
        self.window, self.folder = make_window()
        self.window.show()

    def tearDown(self):
        self.window.close()
        self.folder.cleanup()

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
        from game.config import GameConfig
        self.window.step_delay_ms = 0
        self.window.start_game(GameConfig('self_play', 'easy'))
        self.assertEqual(self.window.navigator.current(), 'game')
        screen = self.window.navigator.screens['game']
        self.window.leave_game()
        self.assertEqual(self.window.navigator.current(), 'home')
        self.assertNotIn('game', self.window.navigator.screens)
        self.assertEqual(screen.session.listeners, [])


    def test_new_game_flow(self):
        self.window.home.new_game_button.click()
        self.assertEqual(self.window.navigator.current(), 'new_game')
        screen = self.window.new_game
        screen.opponent.buttons['friend'].click()
        self.assertFalse(screen.level_card.isVisibleTo(screen))
        screen.opponent.buttons['computer'].click()
        self.assertTrue(screen.level_card.isVisibleTo(screen))
        screen.level.buttons['hard'].click()
        screen.color.buttons['black'].click()
        self.assertEqual(screen.white_name.text(), 'Computer, Hard')
        self.assertEqual(screen.black_name.text(), 'You')
        screen.start_button.click()
        self.assertEqual(self.window.navigator.current(), 'game')
        game = self.window.navigator.screens['game']
        self.assertEqual(game.computer_levels, {1: 'hard'})

    def test_back_from_new_game(self):
        self.window.home.new_game_button.click()
        self.window.new_game.back_button.click()
        self.assertEqual(self.window.navigator.current(), 'home')

    def test_rematch_and_new_game_from_the_result(self):
        from game.config import GameConfig
        self.window.step_delay_ms = 0
        self.window.start_game(GameConfig('friend'))
        first = self.window.navigator.screens['game']
        first.resign(1)
        first.show_result()
        self.assertTrue(first.result_overlay.isVisible())
        first.result_overlay.rematch_button.click()
        second = self.window.navigator.screens['game']
        self.assertIsNot(first, second)
        self.assertEqual(self.window.navigator.current(), 'game')
        second.resign(1)
        second.show_result()
        second.result_overlay.new_game_button.click()
        self.assertEqual(self.window.navigator.current(), 'new_game')
        self.assertNotIn('game', self.window.navigator.screens)
        self.window.new_game.back_button.click()
        self.assertEqual(self.window.navigator.current(), 'home')


    def test_statistics_and_settings_from_home(self):
        self.window.home.statistics_button.click()
        self.assertEqual(self.window.navigator.current(), 'stats')
        self.window.stats_screen.back_button.click()
        self.window.home.settings_button.click()
        self.assertEqual(self.window.navigator.current(), 'settings')
        self.window.settings_screen.back_button.click()
        self.assertEqual(self.window.navigator.current(), 'home')

    def test_new_game_remembers_choices(self):
        self.window.home.new_game_button.click()
        screen = self.window.new_game
        screen.level.buttons['hard'].click()
        screen.color.buttons['random'].click()
        screen.start_button.click()
        self.window.leave_game()
        self.window.home.new_game_button.click()
        self.assertEqual(screen.level.value(), 'hard')
        self.assertEqual(screen.color.value(), 'random')
        self.assertEqual(self.window.settings.get('default_level'), 'hard')

    def test_leaving_a_computer_game_is_a_loss(self):
        from game.config import GameConfig
        self.window.step_delay_ms = 0
        self.window.start_game(GameConfig('computer', 'easy', 'white'))
        self.window.leave_game()
        self.assertEqual(self.window.stats.level('easy'), {'wins': 0, 'losses': 1, 'streak': -1})

    def test_restart_counts_and_finished_game_is_counted_once(self):
        from game.config import GameConfig
        self.window.step_delay_ms = 0
        self.window.start_game(GameConfig('computer', 'medium', 'white'))
        game = self.window.navigator.screens['game']
        game.open_pause()
        game.pause_overlay.restart_button.click()
        self.assertEqual(self.window.stats.level('medium')['losses'], 1)
        game = self.window.navigator.screens['game']
        game.resign(1)
        game.show_result()
        self.assertEqual(self.window.stats.level('medium')['losses'], 2)
        self.assertIn('0 wins and 2 losses', game.result_overlay.record.text())
        self.window.leave_game()
        self.assertEqual(self.window.stats.level('medium')['losses'], 2)

    def test_friend_games_count_when_finished(self):
        from game.config import GameConfig
        self.window.start_game(GameConfig('friend'))
        self.window.leave_game()
        self.assertEqual(self.window.stats.friend_games(), 0)
        self.window.start_game(GameConfig('friend'))
        self.window.navigator.screens['game'].resign(1)
        self.assertEqual(self.window.stats.friend_games(), 1)

    def test_settings_from_the_pause_menu_apply_to_the_game(self):
        from game.config import GameConfig
        self.window.start_game(GameConfig('friend'))
        game = self.window.navigator.screens['game']
        game.session.start(opening=(5, 3))
        self.assertTrue(game.board.view.sources)
        game.open_pause()
        game.pause_overlay.settings_button.click()
        self.assertEqual(self.window.navigator.current(), 'settings')
        self.window.settings_screen.hints.click()
        self.window.settings_screen.back_button.click()
        self.assertEqual(self.window.navigator.current(), 'game')
        game.close_pause()
        self.assertEqual(game.board.view.sources, set())
        game.on_board_click('point', 17)
        game.on_board_click('point', 22)
        self.assertEqual(game.session.board[22], [1, 1])

    def test_speed_setting_reaches_the_computer(self):
        from game.config import GameConfig
        self.window.start_game(GameConfig('computer', 'easy', 'white'))
        game = self.window.navigator.screens['game']
        self.assertEqual(game.ai.step_delay_ms, 500)
        self.window.settings.set('speed', 'slow')
        self.assertEqual(game.ai.step_delay_ms, 900)

    def test_statistics_screen_shows_the_record(self):
        self.window.stats.record_computer_game('hard', True)
        self.window.stats.record_computer_game('hard', False)
        self.window.stats.record_computer_game('easy', True)
        self.window.home.statistics_button.click()
        screen = self.window.stats_screen
        self.assertEqual([t.text() for t in screen.totals], ['3', '67%', '0'])
        cells = screen.rows['hard']
        self.assertEqual((cells[1].text(), cells[2].text(), cells[4].text(), cells[5].text()), ('1', '1', '50%', 'L1'))


class GameConfigTest(unittest.TestCase):
    def test_computer_levels(self):
        import random
        from game.config import GameConfig
        self.assertEqual(GameConfig('friend').computer_levels(), {})
        self.assertEqual(GameConfig('computer', 'hard', 'white').computer_levels(), {-1: 'hard'})
        self.assertEqual(GameConfig('computer', 'easy', 'black').computer_levels(), {1: 'easy'})
        self.assertEqual(GameConfig('self_play', 'medium').computer_levels(), {1: 'medium', -1: 'medium'})
        drawn = {tuple(GameConfig('computer', 'easy', 'random').computer_levels(random.Random(i)))
                 for i in range(20)}
        self.assertEqual(drawn, {(1,), (-1,)})


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



@unittest.skipIf(QApplication is None, 'PyQt6 is not installed')
class OverlayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from ui.screens.game import GameScreen
        self.screen = GameScreen({-1: 'easy'}, step_delay_ms=0)
        self.screen.resize(1280, 800)
        self.screen.show()
        self.session = self.screen.session
        self.session.start(opening=(5, 3))

    def tearDown(self):
        self.screen.shutdown()
        self.screen.close()

    def test_pause_freezes_the_game(self):
        self.screen.open_pause()
        self.assertTrue(self.screen.pause_overlay.isVisible())
        self.assertTrue(self.screen.ai.paused)
        self.screen.on_board_click('point', 17)
        self.assertIsNone(self.screen.selected)
        self.assertEqual(self.screen.board.view.sources, set())
        self.screen.pause_overlay.resume_button.click()
        self.assertFalse(self.screen.pause_overlay.isVisible())
        self.assertFalse(self.screen.ai.paused)
        self.screen.on_board_click('point', 17)
        self.assertEqual(self.screen.selected, 17)

    def test_escape_toggles_pause(self):
        self.screen.toggle_pause()
        self.assertTrue(self.screen.pause_overlay.isVisible())
        self.screen.toggle_pause()
        self.assertFalse(self.screen.pause_overlay.isVisible())

    def test_resign_shows_the_loss(self):
        self.screen.open_pause()
        self.screen.resign(self.screen.resigning_player())
        self.assertFalse(self.screen.pause_overlay.isVisible())
        self.screen.show_result()
        self.assertTrue(self.screen.result_overlay.isVisible())
        title, won, subtitle, tiles = self.screen.result_summary()
        self.assertEqual(title, 'You lost')
        self.assertFalse(won)
        self.assertIn('by resignation', subtitle)
        self.assertIn('on Easy', subtitle)

    def test_win_summary(self):
        board = [[0, 0] for _ in range(26)]
        board[0], board[25] = [0, 1], [0, -1]
        board[24] = [1, 1]
        board[5] = [3, -1]
        from game.session import Phase
        self.session.board, self.session.player, self.session.phase = board, 1, Phase.AWAIT_ROLL
        self.session.roll([6, 3])
        self.session.move(24, 6)
        title, won, subtitle, tiles = self.screen.result_summary()
        self.assertEqual((title, won), ('You won', True))
        self.assertEqual(tiles[2], (15, 'computer pips left'))

    def test_main_menu_leaves(self):
        left = []
        self.screen.leave.connect(lambda: left.append(True))
        self.screen.open_pause()
        self.screen.pause_overlay.menu_button.click()
        self.assertEqual(left, [True])

    def test_no_resign_between_computers(self):
        from ui.screens.game import GameScreen
        screen = GameScreen({1: 'easy', -1: 'easy'}, step_delay_ms=0)
        self.assertTrue(screen.pause_overlay.resign_button.isHidden())
        screen.shutdown()



@unittest.skipIf(QApplication is None, 'PyQt6 is not installed')
class BoardMotionAndKeyboardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from ui.screens.game import GameScreen
        self.screen = GameScreen({})
        self.session = self.screen.session
        self.session.start(opening=(5, 3))
        self.board = self.screen.board

    def tearDown(self):
        self.screen.shutdown()

    def key(self, key):
        self.app.sendEvent(self.board, QKeyEvent(QEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier))

    def wait(self, ms):
        from PyQt6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        QTimer.singleShot(ms, loop.quit)
        loop.exec()

    def test_a_move_slides_and_lands(self):
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 22)
        self.assertEqual(len(self.board.flights), 1)
        flight = self.board.flights[0]
        self.assertEqual((flight.owner, flight.lands_on), (1, ('point', 22)))
        self.assertEqual(self.board.hidden('point', 22), 1)
        self.wait(400)
        self.assertEqual(self.board.flights, [])

    def test_a_hit_slides_to_the_bar(self):
        self.session.board[20] = [1, -1]
        self.session.board[13] = [4, -1]
        self.session.refresh_legal()
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 20)
        self.assertEqual([f.lands_on for f in self.board.flights], [('point', 20), ('bar', -1)])

    def test_a_new_position_ends_the_slide(self):
        self.screen.on_board_click('point', 17)
        self.screen.on_board_click('point', 22)
        self.screen.undo()
        self.assertEqual(self.board.flights, [])

    def test_keyboard_moves_a_checker(self):
        self.key(Qt.Key.Key_Right)
        self.assertEqual(self.board.view.cursor, ('point', 12))
        self.key(Qt.Key.Key_Left)
        self.key(Qt.Key.Key_Left)
        self.assertEqual(self.board.view.cursor, ('point', 19))
        self.key(Qt.Key.Key_Left)
        self.assertEqual(self.board.view.cursor, ('point', 17))
        self.key(Qt.Key.Key_Return)
        self.assertEqual(self.screen.selected, 17)
        self.assertEqual(self.board.view.cursor, ('point', 20))
        self.key(Qt.Key.Key_Right)
        self.key(Qt.Key.Key_Space)
        self.assertEqual(self.session.board[22], [1, 1])
        self.assertIsNone(self.screen.selected)

    def test_escape_cancels_then_pauses(self):
        self.key(Qt.Key.Key_Return)
        self.assertIsNotNone(self.screen.selected)
        self.key(Qt.Key.Key_Escape)
        self.assertIsNone(self.screen.selected)
        self.assertFalse(self.screen.pause_overlay.isVisibleTo(self.screen))
        self.key(Qt.Key.Key_Escape)
        self.assertTrue(self.screen.pause_overlay.isVisibleTo(self.screen))

    def test_keyboard_bears_off_through_the_tray(self):
        from game.session import Phase
        board = [[0, 0] for _ in range(26)]
        board[0], board[25] = [0, 1], [0, -1]
        board[22] = [2, 1]
        board[3] = [2, -1]
        self.session.board, self.session.player, self.session.phase = board, 1, Phase.AWAIT_ROLL
        self.session.roll([6, 2])
        self.key(Qt.Key.Key_Return)
        self.assertEqual(self.screen.candidates(), [('point', 22), ('point', 24), ('tray', None)])
        self.key(Qt.Key.Key_Right)
        self.key(Qt.Key.Key_Return)
        self.assertEqual(self.session.board[22], [1, 1])
        self.assertEqual(self.session.dice_left, [2])

    def test_the_bar_comes_first(self):
        self.session.board[0] = [1, 1]
        self.session.board[1] = [1, 1]
        self.session.refresh_legal()
        self.screen.refresh()
        self.assertEqual(self.screen.candidates(), [('bar', None)])
        self.key(Qt.Key.Key_Return)
        self.assertEqual(self.screen.selected, 0)


if __name__ == '__main__':
    unittest.main()
