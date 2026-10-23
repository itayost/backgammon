from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QFrame

from ui.widgets.basics import button, label, divider
from ui.widgets.overlay import Overlay


class PauseOverlay(Overlay):
    resume = pyqtSignal()
    restart = pyqtSignal()
    settings = pyqtSignal()
    resign = pyqtSignal()
    main_menu = pyqtSignal()

    def __init__(self, parent, can_resign=True, leaving_note=''):
        super().__init__(parent, 400)
        title = label('Paused', 'headline')
        self.body.addWidget(title)
        self.body.addSpacing(8)
        self.resume_button = button('Resume', 'primary', 52)
        self.restart_button = button('Restart with the same setup', 'secondary', 52)
        self.settings_button = button('Settings', 'secondary', 52)
        self.resign_button = button('Resign', 'danger', 52)
        self.menu_button = button('Main menu', 'ghost', 48)
        self.body.addWidget(self.resume_button)
        self.body.addWidget(self.restart_button)
        self.body.addWidget(self.settings_button)
        self.body.addWidget(self.resign_button)
        self.resign_button.setVisible(can_resign)
        self.body.addSpacing(4)
        self.body.addWidget(divider())
        self.body.addSpacing(4)
        self.body.addWidget(self.menu_button)
        note = label(leaving_note, 'muted', wrap=True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setVisible(bool(leaving_note))
        self.body.addWidget(note)

        self.resume_button.clicked.connect(self.resume)
        self.restart_button.clicked.connect(self.restart)
        self.settings_button.clicked.connect(self.settings)
        self.resign_button.clicked.connect(self.resign)
        self.menu_button.clicked.connect(self.main_menu)

    def open(self):
        super().open()
        self.resume_button.setFocus()


class GameOverOverlay(Overlay):
    rematch = pyqtSignal()
    new_game = pyqtSignal()
    main_menu = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent, 480)
        self.body.setSpacing(24)
        head = QVBoxLayout()
        head.setSpacing(8)
        self.title = label('', 'result')
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle = label('', 'muted')
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(self.title)
        head.addWidget(self.subtitle)
        self.body.addLayout(head)

        tiles = QHBoxLayout()
        tiles.setSpacing(12)
        self.tiles = []
        for _ in range(3):
            tile = QFrame()
            tile.setProperty('role', 'tile')
            layout = QVBoxLayout(tile)
            layout.setContentsMargins(8, 14, 8, 14)
            layout.setSpacing(4)
            value = label('', 'number')
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption = label('', 'muted')
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption.setWordWrap(True)
            layout.addWidget(value)
            layout.addWidget(caption)
            tiles.addWidget(tile)
            self.tiles.append((value, caption))
        self.body.addLayout(tiles)
        self.record = label('', 'muted', wrap=True)
        self.record.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.addWidget(self.record)

        self.rematch_button = button('Rematch', 'primary', 56)
        self.new_game_button = button('New game', 'secondary', 52)
        self.menu_button = button('Main menu', 'secondary', 52)
        self.body.addWidget(self.rematch_button)
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(self.new_game_button)
        row.addWidget(self.menu_button)
        self.body.addLayout(row)

        self.rematch_button.clicked.connect(self.rematch)
        self.new_game_button.clicked.connect(self.new_game)
        self.menu_button.clicked.connect(self.main_menu)

    def show_result(self, title, won, subtitle, tiles, record=''):
        """tiles: three (value, caption) pairs, record: the line about the player's record"""
        self.record.setText(record)
        self.record.setVisible(bool(record))
        self.title.setText(title)
        self.title.setProperty('role', 'result-win' if won else 'result')
        self.title.style().unpolish(self.title)
        self.title.style().polish(self.title)
        self.subtitle.setText(subtitle)
        for (value_label, caption_label), (value, caption) in zip(self.tiles, tiles):
            value_label.setText(str(value))
            caption_label.setText(caption)
        self.open()
        self.rematch_button.setFocus()
