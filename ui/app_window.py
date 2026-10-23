import os

from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QMainWindow

from stores.settings_store import SettingsStore
from stores.stats_store import StatsStore
from ui.navigator import Navigator
from ui.screens.home import HomeScreen
from ui.screens.how_to import HowToScreen
from ui.screens.game import GameScreen
from ui.screens.new_game import NewGameScreen
from ui.screens.settings import SettingsScreen
from ui.screens.stats import StatsScreen


def default_stats_path():
    folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return os.path.join(folder, 'stats.json')


class AppWindow(QMainWindow):
    def __init__(self, settings=None, stats=None):
        super().__init__()
        self.setWindowTitle('Backgammon')
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self.navigator = Navigator()
        self.setCentralWidget(self.navigator)

        self.settings = settings or SettingsStore()
        self.stats = stats or StatsStore(default_stats_path())
        # Overrides the computer speed setting, for tests
        self.step_delay_ms = None

        self.home = HomeScreen()
        self.how_to = HowToScreen()
        self.new_game = NewGameScreen(self.settings)
        self.settings_screen = SettingsScreen(self.settings)
        self.stats_screen = StatsScreen(self.stats)
        self.navigator.add_screen('home', self.home)
        self.navigator.add_screen('how_to', self.how_to)
        self.navigator.add_screen('new_game', self.new_game)
        self.navigator.add_screen('settings', self.settings_screen)
        self.navigator.add_screen('stats', self.stats_screen)

        self.home.new_game.connect(self.open_new_game)
        self.home.statistics.connect(self.open_stats)
        self.home.settings.connect(self.open_settings)
        self.home.how_to.connect(lambda: self.navigator.go('how_to'))
        self.home.quit.connect(self.close)
        self.how_to.back.connect(self.navigator.back)
        self.how_to.start.connect(self.open_new_game)
        self.new_game.back.connect(self.navigator.back)
        self.new_game.start.connect(self.start_game)
        self.settings_screen.back.connect(self.navigator.back)
        self.stats_screen.back.connect(self.navigator.back)
        self.settings.changed.connect(self.apply_settings)

        self.navigator.reset('home')

    def open_new_game(self):
        self.new_game.load()
        self.navigator.go('new_game')

    def open_settings(self):
        self.settings_screen.reload()
        self.navigator.go('settings')

    def open_stats(self):
        self.stats_screen.reload()
        self.navigator.go('stats')

    def current_step_delay(self):
        return self.step_delay_ms if self.step_delay_ms is not None else self.settings.step_delay_ms()

    def apply_settings(self, key=None):
        screen = self.navigator.screens.get('game')
        if screen is not None:
            screen.apply_settings(self.settings.get('show_hints'), self.current_step_delay())

    def start_game(self, config):
        """Starts a game for a GameConfig; a random color is drawn again for every game"""
        self.end_game()
        screen = GameScreen(config.computer_levels(), config=config, step_delay_ms=self.current_step_delay(),
                            show_hints=self.settings.get('show_hints'), stats=self.stats)
        screen.leave.connect(self.leave_game)
        screen.open_settings.connect(self.open_settings)
        screen.rematch.connect(lambda: self.start_game(config))
        screen.new_game.connect(self.new_game_from_game)
        self.navigator.add_screen('game', screen)
        self.navigator.reset('game')
        screen.start()

    def new_game_from_game(self):
        self.end_game()
        self.navigator.reset('home')
        self.open_new_game()

    def leave_game(self):
        self.end_game()
        self.navigator.reset('home')

    def end_game(self):
        screen = self.navigator.screens.get('game')
        if screen is not None:
            screen.shutdown()
            self.navigator.remove_screen('game')

    def closeEvent(self, event):
        self.end_game()
        super().closeEvent(event)
