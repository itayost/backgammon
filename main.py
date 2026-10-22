import sys

from PyQt6.QtWidgets import QApplication, QDialog

from gui import BackgammonBoard
from backgammon import backgammon
from controller import controller
from new_game_dialog import NewGameDialog

if __name__ == '__main__':
    app = QApplication(sys.argv)

    dialog = NewGameDialog()
    if dialog.exec() != QDialog.DialogCode.Accepted.value:
        sys.exit(0)
    levels = dialog.computer_levels()

    model = backgammon()
    gui = BackgammonBoard()
    gui.set_computer_players(levels.keys())
    con = controller(model, gui)
    ai = None
    if levels:
        from ai.ai_controller import AIController
        from ai.player import ComputerPlayer
        ai = AIController(model, {player: ComputerPlayer(level) for player, level in levels.items()})
        app.aboutToQuit.connect(ai.wait_for_threads)
    gui.show()
    sys.exit(app.exec())
