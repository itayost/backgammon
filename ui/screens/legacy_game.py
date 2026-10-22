"""Hosts the current board inside the new window until the new game screen replaces it"""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox

from backgammon import backgammon
from controller import controller
from gui import BackgammonBoard
from ui.widgets.basics import button, label


class LegacyGameScreen(QWidget):
    leave = pyqtSignal()

    def __init__(self, computer_levels, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        header.addWidget(label('Backgammon', 'title'))
        header.addStretch(1)
        self.menu_button = button('Main menu', 'secondary', 44)
        header.addWidget(self.menu_button)
        root.addLayout(header)

        self.model = backgammon()
        self.board = BackgammonBoard()
        self.board.set_computer_players(computer_levels.keys())
        self.board.on_quit = self.leave.emit
        root.addWidget(self.board, 1)
        self.controller = controller(self.model, self.board)

        self.ai = None
        if computer_levels:
            from ai.ai_controller import AIController
            from ai.player import ComputerPlayer
            self.ai = AIController(self.model, {player: ComputerPlayer(level)
                                                for player, level in computer_levels.items()})

        self.menu_button.clicked.connect(self.confirm_leave)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.confirm_leave()
        else:
            super().keyPressEvent(event)

    def confirm_leave(self):
        answer = QMessageBox.question(self, 'Leave the game', 'Leaving ends this game. Go to the main menu?')
        if answer == QMessageBox.StandardButton.Yes:
            self.leave.emit()

    def shutdown(self):
        """Stops the computer and detaches everything from the model"""
        if self.ai is not None:
            self.ai.cancel()
            self.ai.wait_for_threads()
        self.model.list_of_controllers.clear()
