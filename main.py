import sys

from PyQt6.QtWidgets import QApplication

from ui import theme
from ui.app_window import AppWindow
from ui.fonts import load_fonts

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName('Backgammon')
    load_fonts()
    app.setStyleSheet(theme.stylesheet())
    window = AppWindow()
    window.show()
    sys.exit(app.exec())
