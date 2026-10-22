from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QStackedWidget


class Navigator(QStackedWidget):
    """Shows one screen at a time and remembers where each screen was opened from,
    so back returns there (Settings opened from a game returns to the game)."""

    changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.screens = {}
        self.history = []

    def add_screen(self, name, widget):
        self.screens[name] = widget
        self.addWidget(widget)

    def remove_screen(self, name):
        widget = self.screens.pop(name, None)
        if widget is not None:
            self.removeWidget(widget)
            widget.deleteLater()
        self.history = [entry for entry in self.history if entry != name]

    def current(self):
        return self.history[-1] if self.history else None

    def go(self, name):
        self.history.append(name)
        self.show_screen(name)

    def reset(self, name):
        """Goes to a screen and forgets the way back, like returning to the main menu"""
        self.history = [name]
        self.show_screen(name)

    def back(self):
        if len(self.history) > 1:
            self.history.pop()
            self.show_screen(self.history[-1])

    def show_screen(self, name):
        widget = self.screens[name]
        self.setCurrentWidget(widget)
        widget.setFocus()
        self.changed.emit(name)
