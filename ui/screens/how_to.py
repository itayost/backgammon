from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGridLayout

from ui import theme
from ui.widgets.basics import button, label, card, divider, icon_button, BACK_ICON

RULES = [
    ('The goal', 'Bring all 15 of your checkers into your home board, then bear them all off. '
                 'The first player to do it wins.'),
    ('Moving', 'Each die is a separate move. Doubles give four moves. You must use as many dice as you can, '
               'and the higher die when only one fits.'),
    ('Points', 'You can land on an empty point, your own point, or a point with one opposing checker. '
               'Two or more opposing checkers block it.'),
    ('Hitting', 'Landing on a single opposing checker sends it to the bar. '
                'It must enter the opponent’s home board before any other move.'),
    ('Bearing off', 'Once all your checkers are home, roll the exact number to take one off, '
                    'or a higher number from your farthest point.'),
    ('No legal move', 'If no move is possible, the turn passes and the board tells you why.'),
]

STEPS = [
    ('Roll', 'Press Roll dice. The dice appear on the board.'),
    ('Select a checker', 'Checkers you can move are highlighted. Click one to select it.'),
    ('Move it', 'Click a highlighted point, or the Off tray to bear off. Click the checker again to cancel.'),
    ('Changed your mind?', 'Undo takes back moves until you finish the turn.'),
    ('Finish', 'Press Done once all the dice you can play are used.'),
]


def step_number(n):
    badge = QLabel(str(n))
    badge.setFixedSize(32, 32)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setStyleSheet(f"background: {theme.color('accent')}; color: {theme.color('accent-ink')}; "
                        f"border-radius: 16px; {theme.font_css(theme.DISPLAY_FONT, 600)} font-size: 16px;")
    return badge


class HowToScreen(QWidget):
    back = pyqtSignal()
    start = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        root = QVBoxLayout(self)
        root.setContentsMargins(96, 40, 96, 40)
        root.setSpacing(28)

        header = QHBoxLayout()
        header.setSpacing(16)
        self.back_button = icon_button(BACK_ICON, 'Back')
        header.addWidget(self.back_button)
        header.addWidget(label('How to play', 'headline'))
        header.addStretch(1)
        root.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(24)

        rules, rules_layout = card(spacing=0)
        rules_layout.addWidget(label('The rules', 'title'))
        rules_layout.addSpacing(8)
        for i, (title, text) in enumerate(RULES):
            if i:
                rules_layout.addWidget(divider())
            rules_layout.addSpacing(10)
            rules_layout.addWidget(label(title, 'label'))
            rules_layout.addWidget(label(text, 'muted', wrap=True))
            rules_layout.addSpacing(10)
        rules_layout.addStretch(1)
        columns.addWidget(rules, 6)

        steps, steps_layout = card(spacing=16)
        steps_layout.addWidget(label('Your turn, step by step', 'title'))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for row, (title, text) in enumerate(STEPS):
            grid.addWidget(step_number(row + 1), row, 0, Qt.AlignmentFlag.AlignTop)
            text_box = QVBoxLayout()
            text_box.setSpacing(2)
            text_box.addWidget(label(title, 'label'))
            text_box.addWidget(label(text, 'muted', wrap=True))
            grid.addLayout(text_box, row, 1)
        grid.setColumnStretch(1, 1)
        steps_layout.addLayout(grid)
        steps_layout.addStretch(1)
        self.start_button = button('Start a game', 'primary', 52)
        steps_layout.addWidget(self.start_button)
        columns.addWidget(steps, 5)

        root.addLayout(columns, 1)

        self.back_button.clicked.connect(self.back)
        self.start_button.clicked.connect(self.start)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.back.emit()
        else:
            super().keyPressEvent(event)
