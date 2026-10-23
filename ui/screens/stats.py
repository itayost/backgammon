from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox

from game.config import LEVELS
from ui import theme
from ui.widgets.basics import button, label, card, divider, icon_button, BACK_ICON


class RateBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rate = 0
        self.setFixedHeight(10)
        self.setMinimumWidth(120)

    def set_rate(self, rate):
        self.rate = rate
        self.setAccessibleName(f'Win rate {rate} percent')
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('line')))
        p.drawRoundedRect(QRectF(self.rect()), 5, 5)
        if self.rate:
            p.setBrush(QColor(theme.color('accent')))
            p.drawRoundedRect(QRectF(0, 0, self.width() * self.rate / 100, self.height()), 5, 5)
        p.end()


def win_rate(wins, games):
    return round(100 * wins / games) if games else 0


def streak_text(streak):
    if streak > 0:
        return f'W{streak}'
    if streak < 0:
        return f'L{-streak}'
    return '-'


class StatsScreen(QWidget):
    back = pyqtSignal()

    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.stats = stats

        root = QVBoxLayout(self)
        root.setContentsMargins(96, 40, 96, 40)
        root.setSpacing(28)
        header = QHBoxLayout()
        header.setSpacing(16)
        self.back_button = icon_button(BACK_ICON, 'Back')
        header.addWidget(self.back_button)
        header.addWidget(label('Statistics', 'headline'))
        header.addStretch(1)
        self.reset_button = button('Reset statistics', 'danger', 44)
        header.addWidget(self.reset_button)
        root.addLayout(header)

        totals = QHBoxLayout()
        totals.setSpacing(20)
        self.totals = []
        for caption in ('GAMES AGAINST THE COMPUTER', 'OVERALL WIN RATE', 'GAMES WITH A FRIEND'):
            box, layout = card(spacing=6)
            layout.addWidget(label(caption, 'caption'))
            value = label('', 'big-number')
            layout.addWidget(value)
            self.totals.append(value)
            totals.addWidget(box, 1)
        root.addLayout(totals)

        table, layout = card(spacing=0)
        layout.addWidget(label('Against the computer, by level', 'title'))
        layout.addSpacing(12)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(14)
        for column, heading in enumerate(('LEVEL', 'WINS', 'LOSSES', 'WIN RATE', '', 'STREAK')):
            grid.addWidget(label(heading, 'caption'), 0, column)
        self.rows = {}
        for row, level in enumerate(LEVELS, start=1):
            cells = [label(level.capitalize(), 'label'), label('', None), label('', None), RateBar(),
                     label('', None), label('', 'muted')]
            for column, cell in enumerate(cells):
                grid.addWidget(cell, row, column)
            self.rows[level] = cells
        grid.setColumnStretch(3, 1)
        layout.addLayout(grid)
        layout.addSpacing(16)
        layout.addWidget(divider())
        layout.addSpacing(12)
        layout.addWidget(label('Finished games count. Resigning or leaving a game against the computer '
                               'counts as a loss.', 'muted', wrap=True))
        root.addWidget(table)
        root.addStretch(1)

        self.back_button.clicked.connect(self.back)
        self.reset_button.clicked.connect(self.confirm_reset)
        self.reload()

    def reload(self):
        games = self.stats.computer_games()
        self.totals[0].setText(str(games))
        self.totals[1].setText(f'{win_rate(self.stats.computer_wins(), games)}%' if games else '-')
        self.totals[2].setText(str(self.stats.friend_games()))
        for level, cells in self.rows.items():
            entry = self.stats.level(level)
            played = entry['wins'] + entry['losses']
            rate = win_rate(entry['wins'], played)
            cells[1].setText(str(entry['wins']))
            cells[2].setText(str(entry['losses']))
            cells[3].set_rate(rate)
            cells[4].setText(f'{rate}%' if played else '-')
            cells[5].setText(streak_text(entry['streak']))

    def confirm_reset(self):
        answer = QMessageBox.question(self, 'Reset statistics', 'Clear all wins, losses and streaks?')
        if answer == QMessageBox.StandardButton.Yes:
            self.stats.reset()
            self.reload()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.back.emit()
        else:
            super().keyPressEvent(event)
