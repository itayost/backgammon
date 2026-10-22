from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QDialogButtonBox

MODES = [("Two players", "two_players"), ("Against the computer", "computer"),
         ("Computer against computer", "computer_vs_computer")]
COLORS = [("Black", -1), ("White", 1)]
LEVELS = [("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")]


class NewGameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Game")

        self.mode = QComboBox()
        self.color = QComboBox()
        self.level = QComboBox()
        for combo, items in ((self.mode, MODES), (self.color, COLORS), (self.level, LEVELS)):
            for text, value in items:
                combo.addItem(text, value)
        self.mode.setCurrentIndex(1)
        self.level.setCurrentIndex(1)
        self.mode.currentIndexChanged.connect(self.update_fields)

        form = QFormLayout()
        form.addRow("Mode:", self.mode)
        form.addRow("Computer plays:", self.color)
        form.addRow("Level:", self.level)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.update_fields()

    def update_fields(self):
        mode = self.mode.currentData()
        self.color.setEnabled(mode == "computer")
        self.level.setEnabled(mode != "two_players")

    def computer_levels(self):
        """Maps every player the computer plays (1 or -1) to its level"""
        mode = self.mode.currentData()
        level = self.level.currentData()
        if mode == "computer":
            return {self.color.currentData(): level}
        if mode == "computer_vs_computer":
            return {1: level, -1: level}
        return {}
