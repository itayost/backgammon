from PyQt6.QtWidgets import QMainWindow

from ui.navigator import Navigator
from ui.screens.home import HomeScreen
from ui.screens.how_to import HowToScreen
from ui.screens.game import GameScreen
from ui.screens.new_game import NewGameScreen


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Backgammon')
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self.navigator = Navigator()
        self.setCentralWidget(self.navigator)

        self.step_delay_ms = 500
        self.home = HomeScreen()
        self.how_to = HowToScreen()
        self.new_game = NewGameScreen()
        self.navigator.add_screen('home', self.home)
        self.navigator.add_screen('how_to', self.how_to)
        self.navigator.add_screen('new_game', self.new_game)

        self.home.new_game.connect(self.open_new_game)
        self.home.how_to.connect(lambda: self.navigator.go('how_to'))
        self.home.quit.connect(self.close)
        self.how_to.back.connect(self.navigator.back)
        self.how_to.start.connect(self.open_new_game)
        self.new_game.back.connect(self.navigator.back)
        self.new_game.start.connect(self.start_game)

        self.navigator.reset('home')

    def open_new_game(self):
        self.navigator.go('new_game')

    def start_game(self, config):
        """Starts a game for a GameConfig; a random color is drawn again for every game"""
        self.end_game()
        screen = GameScreen(config.computer_levels(), config=config, step_delay_ms=self.step_delay_ms)
        screen.leave.connect(self.leave_game)
        screen.rematch.connect(lambda: self.start_game(config))
        screen.new_game.connect(self.new_game_from_game)
        self.navigator.add_screen('game', screen)
        self.navigator.reset('game')
        screen.start()

    def new_game_from_game(self):
        self.end_game()
        self.navigator.reset('home')
        self.navigator.go('new_game')

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
