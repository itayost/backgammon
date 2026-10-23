"""Selectable controls from the mockups: the segmented control and the choice cards"""
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QButtonGroup, QLabel,
                             QSizePolicy)

from ui import theme


class SegmentedControl(QFrame):
    changed = pyqtSignal(object)

    def __init__(self, options, value=None, accessible_name='', parent=None):
        """options: list of (label, value)"""
        super().__init__(parent)
        self.setProperty('role', 'segments')
        self.setAccessibleName(accessible_name)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for text, option in options:
            b = QPushButton(text)
            b.setProperty('variant', 'segment')
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setAccessibleName(f'{accessible_name}: {text}' if accessible_name else text)
            b.clicked.connect(lambda checked, o=option: self.changed.emit(o))
            self.group.addButton(b)
            self.buttons[option] = b
            layout.addWidget(b)
        self.set_value(value if value is not None else options[0][1])

    def set_value(self, value):
        self.buttons[value].setChecked(True)

    def value(self):
        for option, b in self.buttons.items():
            if b.isChecked():
                return option


class CheckerDot(QWidget):
    """A small checker swatch: 1 white, -1 black, None for random (half and half)"""

    def __init__(self, player, size=28, parent=None):
        super().__init__(parent)
        self.player = player
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rim = self.width() * 0.1
        r = self.width() / 2 - rim / 2
        center = QPointF(self.width() / 2, self.height() / 2)
        if self.player is None:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.color('checker-white')))
            p.drawPie(0, 0, self.width(), self.height(), 90 * 16, 180 * 16)
            p.setBrush(QColor(theme.color('checker-black')))
            p.drawPie(0, 0, self.width(), self.height(), 270 * 16, 180 * 16)
            p.setPen(QPen(QColor(theme.color('text-muted')), rim))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(center, r, r)
        else:
            kind = 'white' if self.player == 1 else 'black'
            p.setPen(QPen(QColor(theme.color(f'checker-{kind}-rim')), rim))
            p.setBrush(QColor(theme.color(f'checker-{kind}')))
            p.drawEllipse(center, r, r)
        p.end()


class ChoiceGroup(QWidget):
    """A row of large selectable cards, each a title with an optional description or a checker swatch"""
    changed = pyqtSignal(object)

    def __init__(self, options, value=None, accessible_name='', columns_stretch=True, parent=None):
        """options: list of dicts with label, value, and text or player"""
        super().__init__(parent)
        self.setAccessibleName(accessible_name)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.buttons = {}
        for option in options:
            b = QPushButton()
            b.setProperty('variant', 'choice')
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setAccessibleName(option['label'])
            inner = QHBoxLayout(b)
            inner.setContentsMargins(16, 14, 18, 14)
            inner.setSpacing(12)
            if 'player' in option:
                inner.addWidget(CheckerDot(option['player']))
            texts = QVBoxLayout()
            texts.setSpacing(4)
            title = QLabel(option['label'])
            title.setProperty('role', 'choice-title')
            title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            texts.addWidget(title)
            if option.get('text'):
                text = QLabel(option['text'])
                text.setProperty('role', 'muted')
                text.setWordWrap(True)
                text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                texts.addWidget(text)
            inner.addLayout(texts, 1)
            b.setProperty('tall', bool(option.get('text')))
            b.clicked.connect(lambda checked, o=option['value']: self.changed.emit(o))
            self.group.addButton(b)
            self.buttons[option['value']] = b
            layout.addWidget(b, 1 if columns_stretch else 0)
        if not columns_stretch:
            layout.addStretch(1)
        self.set_value(value if value is not None else options[0]['value'])

    def set_value(self, value):
        self.buttons[value].setChecked(True)

    def value(self):
        for option, b in self.buttons.items():
            if b.isChecked():
                return option


class Switch(QPushButton):
    """An on and off switch: an amber pill with the knob on the right when on"""

    def __init__(self, accessible_name, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(52, 30)
        self.setProperty('variant', 'switch')
        self.setAccessibleName(accessible_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        on = self.isChecked()
        if self.hasFocus():
            p.setPen(QPen(QColor(theme.color('text') if on else theme.color('accent')), 2))
        else:
            p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('accent' if on else 'line')))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 14, 14)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.color('accent-ink' if on else 'text-muted')))
        knob_x = self.width() - 15 if on else 15
        p.drawEllipse(QPointF(knob_x, self.height() / 2), 12, 12)
        p.end()
