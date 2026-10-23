from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from ui.widgets.basics import label, card, divider, icon_button, BACK_ICON
from ui.widgets.choices import SegmentedControl, Switch


class SettingsScreen(QWidget):
    back = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.settings = settings

        root = QVBoxLayout(self)
        root.setContentsMargins(96, 40, 96, 40)
        root.setSpacing(28)
        header = QHBoxLayout()
        header.setSpacing(16)
        self.back_button = icon_button(BACK_ICON, 'Back')
        header.addWidget(self.back_button)
        header.addWidget(label('Settings', 'headline'))
        header.addStretch(1)
        header.addWidget(label('Changes apply right away. Back returns to where you came from.', 'muted'))
        root.addLayout(header)

        gameplay, layout = card(spacing=0)
        gameplay.setMaximumWidth(720)
        layout.addWidget(label('Gameplay', 'title'))
        layout.addSpacing(8)

        self.hints = Switch('Show legal moves', settings.get('show_hints'))
        self.add_row(layout, 'Show legal moves', 'Highlight the checkers you can move and where they can go.',
                     self.hints, inline=True)
        self.speed = SegmentedControl([('Slow', 'slow'), ('Normal', 'normal'), ('Fast', 'fast')],
                                      settings.get('speed'), 'Computer move speed')
        self.add_row(layout, 'Computer move speed', 'How long the computer pauses between its checker moves.',
                     self.speed)
        self.level = SegmentedControl([('Easy', 'easy'), ('Medium', 'medium'), ('Hard', 'hard')],
                                      settings.get('default_level'), 'Default level')
        self.add_row(layout, 'Default level', 'Preselected when you start a new game.', self.level)
        self.color = SegmentedControl([('White', 'white'), ('Black', 'black'), ('Random', 'random')],
                                      settings.get('default_color'), 'Default color')
        self.add_row(layout, 'Default color', 'The color you play when you start a new game.', self.color,
                     last=True)
        root.addWidget(gameplay)
        root.addWidget(label('Board themes and sound effects are planned for a later version.', 'muted'))
        root.addStretch(1)

        self.hints.toggled.connect(lambda on: settings.set('show_hints', on))
        self.speed.changed.connect(lambda value: settings.set('speed', value))
        self.level.changed.connect(lambda value: settings.set('default_level', value))
        self.color.changed.connect(lambda value: settings.set('default_color', value))
        self.back_button.clicked.connect(self.back)

    @staticmethod
    def add_row(layout, title, text, control, inline=False, last=False):
        row = QVBoxLayout()
        row.setContentsMargins(0, 16, 0, 16)
        row.setSpacing(10)
        texts = QVBoxLayout()
        texts.setSpacing(2)
        texts.addWidget(label(title, 'label'))
        texts.addWidget(label(text, 'muted'))
        if inline:
            line = QHBoxLayout()
            line.addLayout(texts, 1)
            line.addWidget(control)
            row.addLayout(line)
        else:
            row.addLayout(texts)
            row.addWidget(control)
        layout.addLayout(row)
        if not last:
            layout.addWidget(divider())

    def reload(self):
        """Shows the stored values, which New game may have changed"""
        self.hints.setChecked(self.settings.get('show_hints'))
        self.speed.set_value(self.settings.get('speed'))
        self.level.set_value(self.settings.get('default_level'))
        self.color.set_value(self.settings.get('default_color'))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.back.emit()
        else:
            super().keyPressEvent(event)
