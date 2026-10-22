"""Small building blocks styled by the stylesheet in ui/theme.py"""
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPainter, QPen, QPixmap, QColor, QPainterPath
from PyQt6.QtWidgets import QPushButton, QLabel, QFrame, QVBoxLayout

from ui import theme


def button(text, variant='secondary', height=48):
    b = QPushButton(text)
    b.setProperty('variant', variant)
    b.setMinimumHeight(height)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def label(text, role=None, wrap=False):
    lb = QLabel(text)
    if role:
        lb.setProperty('role', role)
    lb.setWordWrap(wrap)
    return lb


def card(padding=24, spacing=12):
    frame = QFrame()
    frame.setProperty('role', 'card')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(spacing)
    return frame, layout


def divider():
    line = QFrame()
    line.setProperty('role', 'divider')
    return line


def stroke_icon(paths, size=20, color=None):
    """An icon drawn from line segments on a 24 unit grid, like the stroke icons in the mockups"""
    color = color or theme.color('text')
    scale = 4
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 2 * size * scale / 24)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    factor = size * scale / 24
    for points in paths:
        path = QPainterPath()
        path.moveTo(points[0][0] * factor, points[0][1] * factor)
        for x, y in points[1:]:
            path.lineTo(x * factor, y * factor)
        painter.drawPath(path)
    painter.end()
    return QIcon(pixmap)


BACK_ICON = [[(15, 18), (9, 12), (15, 6)]]
MENU_ICON = [[(4, 7), (20, 7)], [(4, 12), (20, 12)], [(4, 17), (20, 17)]]


def icon_button(paths, accessible_name):
    b = QPushButton()
    b.setProperty('variant', 'icon')
    b.setIcon(stroke_icon(paths))
    b.setIconSize(QSize(20, 20))
    b.setAccessibleName(accessible_name)
    b.setToolTip(accessible_name)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b
