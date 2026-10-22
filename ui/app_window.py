from PyQt6.QtWidgets import QMainWindow, QDialog

from ui.navigator import Navigator
from ui.screens.home import HomeScreen
from ui.screens.how_to import HowToScreen
from ui.screens.legacy_game import LegacyGameScreen


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Backgammon')
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)

        self.navigator = Navigator()
        self.setCentralWidget(self.navigator)

        self.home = HomeScreen()
        self.how_to = HowToScreen()
        self.navigator.add_screen('home', self.home)
        self.navigator.add_screen('how_to', self.how_to)

        self.home.new_game.connect(self.ask_new_game)
        self.home.how_to.connect(lambda: self.navigator.go('how_to'))
        self.home.quit.connect(self.close)
        self.how_to.back.connect(self.navigator.back)
        self.how_to.start.connect(self.ask_new_game)

        self.navigator.reset('home')

    def ask_new_game(self):
        from new_game_dialog import NewGameDialog
        dialog = NewGameDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted.value:
            self.start_game(dialog.computer_levels())

    def start_game(self, computer_levels):
        self.end_game()
        screen = LegacyGameScreen(computer_levels)
        screen.leave.connect(self.leave_game)
        self.navigator.add_screen('game', screen)
        self.navigator.go('game')

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
