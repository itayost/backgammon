from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy

import rules
from ui import theme
from ui.board import layout as L

PIPS = {1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8]}


@dataclass
class BoardView:
    """Everything the board draws; the game screen builds it from the session"""
    board: list = field(default_factory=rules.init_board)
    dice: list = field(default_factory=list)      # (value, used)
    sources: set = field(default_factory=set)     # points (0 and 25 for the bars) with a movable checker
    selected: int = None
    targets: set = field(default_factory=set)     # points the selected checker can reach
    tray_target: bool = False                     # the selected checker can bear off
    player: int = 1


def qcolor(name, alpha=None):
    c = QColor(theme.color(name))
    if alpha is not None:
        c.setAlphaF(alpha)
    return c


class BoardWidget(QWidget):
    clicked = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = BoardView()
        self.setMinimumSize(L.W // 2, L.H // 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName('Backgammon board')
        self.setMouseTracking(True)

    def set_view(self, view):
        self.view = view
        self.update()

    # Coordinates

    def scale_and_origin(self):
        scale = min(self.width() / L.W, self.height() / L.H)
        return scale, (self.width() - L.W * scale) / 2, (self.height() - L.H * scale) / 2

    def to_board(self, pos):
        scale, ox, oy = self.scale_and_origin()
        return (pos.x() - ox) / scale, (pos.y() - oy) / scale

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        target = L.hit_test(*self.to_board(event.position()))
        if target is not None:
            self.clicked.emit(*target)

    def mouseMoveEvent(self, event):
        target = L.hit_test(*self.to_board(event.position()))
        self.setCursor(Qt.CursorShape.PointingHandCursor if self.is_clickable(target)
                       else Qt.CursorShape.ArrowCursor)

    def is_clickable(self, target):
        if target is None:
            return False
        kind, point = target
        v = self.view
        if kind == 'point':
            return point in v.sources or point in v.targets
        if kind == 'bar':
            return rules.bar_of(v.player) in v.sources
        return v.tray_target

    # Painting

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        scale, ox, oy = self.scale_and_origin()
        p.translate(ox, oy)
        p.scale(scale, scale)
        self.paint_frame(p)
        for point in range(1, 25):
            self.paint_point(p, point)
        for point in range(1, 25):
            self.paint_stack(p, point)
        self.paint_bar(p)
        self.paint_tray(p)
        self.paint_dice(p)
        p.end()

    def paint_frame(self, p):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(qcolor('board-frame'))
        p.drawRoundedRect(QRectF(0, 0, L.W, L.H), 16, 16)
        p.setBrush(qcolor('board-felt'))
        for x in (L.LEFT_X, L.RIGHT_X):
            p.drawRoundedRect(QRectF(x, L.PAD, L.FIELD_W, L.H - 2 * L.PAD), 8, 8)
        p.setBrush(qcolor('board-bar'))
        p.drawRoundedRect(QRectF(L.BAR_X, L.PAD, L.BAR_W, L.H - 2 * L.PAD), 6, 6)
        p.drawRoundedRect(QRectF(L.TRAY_X, L.PAD, L.TRAY_W, L.H - 2 * L.PAD), 6, 6)

    def paint_point(self, p, point):
        x, y, w, h, top = L.point_rect(point)
        if point in self.view.targets:
            color = qcolor('accent')
        else:
            color = qcolor('point-dark' if point % 2 == 0 else 'point-light')
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(color)
        if top:
            poly = QPolygonF([QPointF(x, y), QPointF(x + w, y), QPointF(x + w / 2, y + h)])
        else:
            poly = QPolygonF([QPointF(x, y + h), QPointF(x + w, y + h), QPointF(x + w / 2, y)])
        p.drawPolygon(poly)

    def paint_stack(self, p, point):
        count, owner = self.view.board[point]
        shown = min(count, L.MAX_SHOWN)
        for slot in range(shown):
            center = QPointF(*L.checker_center(point, slot))
            is_top = slot == shown - 1
            ring = None
            if is_top and point == self.view.selected:
                ring = 'selected'
            elif is_top and point in self.view.sources and self.view.selected is None:
                ring = 'movable'
            label = str(count) if is_top and count > L.MAX_SHOWN else None
            self.paint_checker(p, center, L.CHECKER, owner, ring, label)
        if point in self.view.targets and shown < L.MAX_SHOWN:
            self.paint_landing(p, QPointF(*L.checker_center(point, shown)))

    def paint_checker(self, p, center, size, owner, ring=None, label=None):
        kind = 'white' if owner == 1 else 'black'
        radius = size / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(0, 0, 0, 90))
        p.drawEllipse(center + QPointF(0, 2), radius, radius)
        rim = size * 0.06
        p.setPen(QPen(qcolor(f'checker-{kind}-rim'), rim))
        p.setBrush(qcolor(f'checker-{kind}'))
        p.drawEllipse(center, radius - rim / 2, radius - rim / 2)
        if ring == 'selected':
            p.setPen(QPen(qcolor('accent'), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(center, radius + 2.5, radius + 2.5)
        elif ring == 'movable':
            p.setPen(QPen(qcolor('accent', 0.75), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(center, radius + 2, radius + 2)
        if label:
            font = QFont(theme.FAMILIES[(theme.DISPLAY_FONT, 600)])
            font.setPixelSize(int(size * 0.36))
            p.setFont(font)
            p.setPen(qcolor('accent-ink' if owner == 1 else 'text'))
            p.drawText(QRectF(center.x() - radius, center.y() - radius, size, size),
                       Qt.AlignmentFlag.AlignCenter, label)

    def paint_landing(self, p, center):
        pen = QPen(qcolor('accent-ink'), 2, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.setBrush(qcolor('accent-ink', 0.12))
        p.drawEllipse(center, L.CHECKER / 2 - 1, L.CHECKER / 2 - 1)

    def paint_bar(self, p):
        for player in (1, -1):
            bar = rules.bar_of(player)
            count = self.view.board[bar][0]
            for slot in range(min(count, 4)):
                is_top = slot == min(count, 4) - 1
                ring = None
                if is_top and self.view.selected == bar:
                    ring = 'selected'
                elif is_top and bar in self.view.sources and self.view.selected is None:
                    ring = 'movable'
                label = str(count) if is_top and count > 4 else None
                self.paint_checker(p, QPointF(*L.bar_center(player, slot)), L.BAR_CHECKER, player, ring, label)

    def paint_tray(self, p):
        if self.view.tray_target:
            x, y, w, h = L.tray_rect(self.view.player)
            p.setPen(QPen(qcolor('accent'), 2))
            p.setBrush(qcolor('accent', 0.12))
            p.drawRoundedRect(QRectF(x + 1, y + 1, w - 2, h - 2), 6, 6)
        font = QFont(theme.FAMILIES[(theme.BODY_FONT, 600)])
        font.setPixelSize(11)
        for player in (1, -1):
            off = rules.borne_off(self.view.board, player)
            kind = 'white' if player == 1 else 'black'
            p.setPen(QPen(qcolor(f'checker-{kind}-rim'), 1))
            p.setBrush(qcolor(f'checker-{kind}'))
            for index in range(off):
                p.drawRoundedRect(QRectF(*L.slab_rect(player, index)), 3, 3)
            x, y, w, h = L.tray_rect(player)
            label_y = y + h - 26 if player == 1 else y + 6
            p.setFont(font)
            p.setPen(qcolor('point-light'))
            p.drawText(QRectF(x, label_y, w, 20), Qt.AlignmentFlag.AlignCenter, f'OFF {off}')

    def paint_dice(self, p):
        for (value, used), (cx, cy) in zip(self.view.dice, L.dice_centers(len(self.view.dice))):
            p.save()
            p.setOpacity(0.35 if used else 1.0)
            rect = QRectF(cx - L.DIE / 2, cy - L.DIE / 2, L.DIE, L.DIE)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(0, 0, 0, 100))
            p.drawRoundedRect(rect.translated(0, 4), 10, 10)
            p.setBrush(qcolor('checker-white'))
            p.drawRoundedRect(rect, 10, 10)
            p.setBrush(qcolor('accent-ink'))
            cell = (L.DIE - 14) / 3
            for index in PIPS[value]:
                px = rect.left() + 7 + (index % 3 + 0.5) * cell
                py = rect.top() + 7 + (index // 3 + 0.5) * cell
                p.drawEllipse(QPointF(px, py), 4, 4)
            p.restore()
