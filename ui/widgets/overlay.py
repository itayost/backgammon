from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect


class Overlay(QWidget):
    """Covers its parent with the night scrim and centers a dialog card on it.
    The board stays visible behind, dimmed and out of play."""

    def __init__(self, parent, width=400):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        row = QHBoxLayout()
        row.addStretch(1)
        self.card = QFrame()
        self.card.setProperty('role', 'dialog')
        self.card.setFixedWidth(width)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.card.setGraphicsEffect(shadow)
        self.body = QVBoxLayout(self.card)
        self.body.setContentsMargins(32, 32, 32, 32)
        self.body.setSpacing(12)
        row.addWidget(self.card)
        row.addStretch(1)
        outer.addStretch(1)
        outer.addLayout(row)
        outer.addStretch(1)
        parent.installEventFilter(self)
        self.hide()

    def eventFilter(self, watched, event):
        if watched is self.parent() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parent().rect())
        return False

    def open(self):
        self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(5, 10, 11, 184))
        p.end()

    def mousePressEvent(self, event):
        # Clicks on the scrim must not reach the board
        event.accept()
