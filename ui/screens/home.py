from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPolygonF, QPen
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect, QSizePolicy)

from ui import theme
from ui.widgets.basics import button, label

# Checkers on the decorative board, (white, black) per point, left to right
TOP_ROW = [(0, 3), (0, 0), (2, 0), (0, 0), (0, 0), (0, 2)]
BOTTOM_ROW = [(3, 0), (0, 0), (0, 1), (2, 0), (0, 0), (3, 0)]
DICE = [(6, -8), (3, 6)]
PIPS = {3: [0, 4, 8], 6: [0, 2, 3, 5, 6, 8]}


class BoardArt(QWidget):
    """A corner of the board, purely decorative, painted with the board tokens"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(360, 420)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName('')
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.setGraphicsEffect(shadow)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Keep the 520 x 600 proportions of the mockup inside the available space
        w = min(self.width() - 20, (self.height() - 40) * 520 / 600)
        h = w * 600 / 520
        s = w / 520
        frame = QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('board-frame')))
        p.drawRoundedRect(frame, 24 * s, 24 * s)
        felt = frame.adjusted(16 * s, 16 * s, -16 * s, -16 * s)
        p.setBrush(QColor(theme.color('board-felt')))
        p.drawRoundedRect(felt, 12 * s, 12 * s)

        inner = felt.adjusted(14 * s, 14 * s, -14 * s, -14 * s)
        gap = 6 * s
        col = (inner.width() - 5 * gap) / 6
        row_h = 228 * s
        checker = min(66 * s, col)
        for i in range(6):
            x = inner.left() + i * (col + gap)
            dark = i % 2 == 0
            self.point(p, QRectF(x, inner.top(), col, row_h), dark, down=True)
            self.point(p, QRectF(x, inner.bottom() - row_h, col, row_h), not dark, down=False)
            self.stack(p, x + col / 2, inner.top(), checker, TOP_ROW[i], down=True)
            self.stack(p, x + col / 2, inner.bottom(), checker, BOTTOM_ROW[i], down=False)

        size = 56 * s
        cx, cy = inner.center().x(), inner.center().y()
        for k, (value, tilt) in enumerate(DICE):
            self.die(p, QPointF(cx + (k - 0.5) * (size + 14 * s), cy), size, value, tilt)
        p.end()

    @staticmethod
    def point(p, rect, dark, down):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('point-dark' if dark else 'point-light')))
        if down:
            poly = QPolygonF([rect.topLeft(), rect.topRight(), QPointF(rect.center().x(), rect.bottom())])
        else:
            poly = QPolygonF([rect.bottomLeft(), rect.bottomRight(), QPointF(rect.center().x(), rect.top())])
        p.drawPolygon(poly)

    @staticmethod
    def stack(p, cx, edge, size, counts, down):
        white, black = counts
        kinds = ['white'] * white + ['black'] * black
        for n, kind in enumerate(kinds):
            offset = n * (size + 2) + size / 2
            cy = edge + offset if down else edge - offset
            rim = size * 0.06
            p.setPen(QPen(QColor(theme.color(f'checker-{kind}-rim')), rim))
            p.setBrush(QColor(theme.color(f'checker-{kind}')))
            p.drawEllipse(QPointF(cx, cy), size / 2 - rim / 2, size / 2 - rim / 2)

    @staticmethod
    def die(p, center, size, value, tilt):
        p.save()
        p.translate(center)
        p.rotate(tilt)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('checker-white')))
        p.drawRoundedRect(QRectF(-size / 2, -size / 2, size, size), size * 0.2, size * 0.2)
        p.setBrush(QColor(theme.color('accent-ink')))
        cell = (size - size * 0.28) / 3
        start = -size / 2 + size * 0.14
        for index in PIPS[value]:
            px = start + (index % 3 + 0.5) * cell
            py = start + (index // 3 + 0.5) * cell
            p.drawEllipse(QPointF(px, py), size * 0.08, size * 0.08)
        p.restore()


class HomeScreen(QWidget):
    new_game = pyqtSignal()
    statistics = pyqtSignal()
    how_to = pyqtSignal()
    settings = pyqtSignal()
    quit = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('screen')
        layout = QHBoxLayout(self)
        layout.setContentsMargins(96, 64, 96, 64)
        layout.setSpacing(64)

        left = QVBoxLayout()
        left.setSpacing(40)
        left.addStretch(1)
        intro = QVBoxLayout()
        intro.setSpacing(16)
        intro.addWidget(label('TWO PLAYERS OR AGAINST THE COMPUTER', 'kicker'))
        intro.addWidget(label('Backgammon', 'wordmark'))
        lead = label('Play a friend on this computer, or take on the computer at easy, medium or hard.', 'lead', wrap=True)
        lead.setMaximumWidth(440)
        intro.addWidget(lead)
        left.addLayout(intro)

        menu = QVBoxLayout()
        menu.setSpacing(12)
        self.new_game_button = button('New game', 'primary', 56)
        self.statistics_button = button('Statistics', 'secondary', 52)
        self.how_to_button = button('How to play', 'secondary', 52)
        self.settings_button = button('Settings', 'secondary', 52)
        self.quit_button = button('Quit', 'ghost', 48)
        for b in (self.new_game_button, self.statistics_button, self.how_to_button, self.settings_button,
                  self.quit_button):
            b.setFixedWidth(320)
            menu.addWidget(b)
        left.addLayout(menu)
        left.addStretch(1)
        layout.addLayout(left, 1)

        self.art = BoardArt()
        self.art.setMaximumWidth(560)
        layout.addWidget(self.art, 1)

        self.new_game_button.clicked.connect(self.new_game)
        self.statistics_button.clicked.connect(self.statistics)
        self.how_to_button.clicked.connect(self.how_to)
        self.settings_button.clicked.connect(self.settings)
        self.quit_button.clicked.connect(self.quit)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
