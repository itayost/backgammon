from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout

from game.config import GameConfig
from ui.widgets.basics import button, label, card, icon_button, BACK_ICON
from ui.widgets.choices import SegmentedControl, ChoiceGroup

LEVEL_TEXT = {
    'easy': 'Plays sensible moves with some randomness. Good for learning.',
    'medium': 'Picks the best move it can see for each roll.',
    'hard': 'Also looks at every reply you could roll. Thinks up to 2.5 seconds.',
}


class NewGameScreen(QWidget):
    back = pyqtSignal()
    start = pyqtSignal(object)  # GameConfig

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.settings = settings
        self.config = self.saved_config()

        root = QVBoxLayout(self)
        root.setContentsMargins(96, 40, 96, 40)
        root.setSpacing(28)
        header = QHBoxLayout()
        header.setSpacing(16)
        self.back_button = icon_button(BACK_ICON, 'Back')
        header.addWidget(self.back_button)
        header.addWidget(label('New game', 'headline'))
        header.addStretch(1)
        root.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(32)
        left = QVBoxLayout()
        left.setSpacing(20)

        opponent_card, opponent_layout = card(spacing=14)
        opponent_layout.addWidget(label('Opponent', 'title'))
        self.opponent = ChoiceGroup([
            {'label': 'Computer', 'value': 'computer', 'text': 'Play against the computer at the level you choose.'},
            {'label': 'Friend on this computer', 'value': 'friend', 'text': 'Two players take turns on the same board.'},
        ], self.config.opponent if self.config.opponent != 'self_play' else 'computer', 'Opponent')
        opponent_layout.addWidget(self.opponent)
        left.addWidget(opponent_card)

        self.level_card, level_layout = card(spacing=14)
        level_layout.addWidget(label('Level', 'title'))
        self.level = SegmentedControl([('Easy', 'easy'), ('Medium', 'medium'), ('Hard', 'hard')],
                                      self.config.level, 'Level')
        level_layout.addWidget(self.level)
        self.level_text = label('', 'muted', wrap=True)
        level_layout.addWidget(self.level_text)
        left.addWidget(self.level_card)

        color_card, color_layout = card(spacing=14)
        self.color_title = label('Your color', 'title')
        color_layout.addWidget(self.color_title)
        self.color = ChoiceGroup([
            {'label': 'White', 'value': 'white', 'player': 1},
            {'label': 'Black', 'value': 'black', 'player': -1},
            {'label': 'Random', 'value': 'random', 'player': None},
        ], self.config.color, 'Color', columns_stretch=False)
        for b in self.color.buttons.values():
            b.setMinimumWidth(140)
        color_layout.addWidget(self.color)
        left.addWidget(color_card)
        left.addStretch(1)
        columns.addLayout(left, 1)

        summary, summary_layout = card(spacing=20)
        summary.setFixedWidth(360)
        summary_layout.addWidget(label('SUMMARY', 'caption'))
        rows = QGridLayout()
        rows.setVerticalSpacing(12)
        rows.setHorizontalSpacing(16)
        self.white_name = label('', 'label')
        self.black_name = label('', 'label')
        for row, (name, value) in enumerate((('White', self.white_name), ('Black', self.black_name),
                                             ('First move', label('Opening roll', 'label')))):
            rows.addWidget(label(name, 'muted'), row, 0)
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            rows.addWidget(value, row, 1)
        summary_layout.addLayout(rows)
        self.start_button = button('Start game', 'primary', 56)
        summary_layout.addWidget(self.start_button)
        summary_layout.addWidget(label('Each side rolls one die; the higher die moves first with both dice. '
                                       'These choices are remembered for next time.', 'muted', wrap=True))
        summary_column = QVBoxLayout()
        summary_column.addWidget(summary)
        summary_column.addStretch(1)
        columns.addLayout(summary_column)
        root.addLayout(columns, 1)

        self.opponent.changed.connect(lambda value: self.update_config(opponent=value))
        self.level.changed.connect(lambda value: self.update_config(level=value))
        self.color.changed.connect(lambda value: self.update_config(color=value))
        self.back_button.clicked.connect(self.back)
        self.start_button.clicked.connect(self.start_game)
        self.refresh()

    def saved_config(self):
        if self.settings is None:
            return GameConfig()
        return GameConfig(self.settings.get('default_opponent'), self.settings.get('default_level'),
                          self.settings.get('default_color'))

    def load(self):
        """Shows the remembered choices, called whenever the screen opens"""
        self.config = self.saved_config()
        self.opponent.set_value(self.config.opponent)
        self.level.set_value(self.config.level)
        self.color.set_value(self.config.color)
        self.refresh()

    def start_game(self):
        config = self.current_config()
        if self.settings is not None:
            self.settings.set('default_opponent', config.opponent)
            self.settings.set('default_level', config.level)
            self.settings.set('default_color', config.color)
        self.start.emit(config)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.back.emit()
        else:
            super().keyPressEvent(event)

    def current_config(self):
        return GameConfig(self.config.opponent, self.config.level, self.config.color)

    def update_config(self, **changes):
        for key, value in changes.items():
            setattr(self.config, key, value)
        self.refresh()

    def refresh(self):
        vs_computer = self.config.opponent == 'computer'
        self.level_card.setVisible(vs_computer)
        self.level_text.setText(LEVEL_TEXT[self.config.level])
        self.color_title.setText('Your color' if vs_computer else 'Player 1 color')
        me = 'You' if vs_computer else 'Player 1'
        other = f'Computer, {self.config.level.capitalize()}' if vs_computer else 'Player 2'
        if self.config.color == 'random':
            white, black = 'Drawn at random', 'Drawn at random'
        elif self.config.color == 'white':
            white, black = me, other
        else:
            white, black = other, me
        self.white_name.setText(white)
        self.black_name.setText(black)
