import sys

from PyQt6.QtWidgets import QApplication

from gui import BackgammonBoard
from backgammon import backgammon
from controller import controller

if __name__ == '__main__':
    app = QApplication(sys.argv)
    model = backgammon()
    gui = BackgammonBoard()
    con = controller(model, gui)
    gui.show()
    sys.exit(app.exec())
