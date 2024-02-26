from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton


class WinnerDialog(QDialog):
    def __init__(self, winner, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Game Over")
        self.setGeometry(200, 200, 400, 200)

        layout = QVBoxLayout()

        message_label = QLabel(f"Player {winner} won! Would you like to play again?")
        layout.addWidget(message_label)

        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(self.accept)
        layout.addWidget(yes_button)

        no_button = QPushButton("No")
        no_button.clicked.connect(self.reject)
        layout.addWidget(no_button)

        self.setLayout(layout)
