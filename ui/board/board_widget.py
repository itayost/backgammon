from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygonF, QFont
from PyQt6.QtWidgets import QWidget, QSizePolicy

import rules
from ui import theme
from ui.board import layout as L

PIPS = {1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8]}
SLIDE_MS = 180
BAR_SHOWN = 4


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
    cursor: tuple = None                          # keyboard cursor: ('point', n), ('bar', None) or ('tray', None)


@dataclass
class Flight:
    """A checker sliding from start to end; its place at the end stays empty until it lands"""
    owner: int
    start: tuple
    end: tuple
    start_size: float
    end_size: float
    lands_on: tuple   # ('point', n), ('bar', player) or ('off', player)


def qcolor(name, alpha=None):
    c = QColor(theme.color(name))
    if alpha is not None:
        c.setAlphaF(alpha)
    return c


class BoardWidget(QWidget):
    clicked = pyqtSignal(str, object)
    navigate = pyqtSignal(int)
    activate = pyqtSignal()
    cancel = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = BoardView()
        self.setMinimumSize(L.W // 2, L.H // 2)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName('Backgammon board')
        self.setAccessibleDescription('Arrow keys choose a checker or a point, Enter picks it, Escape cancels.')
        self.setMouseTracking(True)
        # Reached with Tab only, so mouse players never see the keyboard cursor
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.flights = []
        self.flight_board = None
        self.progress = 1.0
        self.animation = QVariantAnimation(self)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(SLIDE_MS)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.on_progress)
        self.animation.finished.connect(self.land)

    def set_view(self, view):
        if self.flights and view.board != self.flight_board:
            # The position moved on before the slide ended, show where things are now
            self.animation.stop()
            self.land()
        self.view = view
        self.update()

    # Sliding checkers

    def animate_step(self, before, after, player, start, end, hit):
        """Slides the checker that moved from start to end (None: borne off) and a hit checker to the bar"""
        if self.flights:
            self.animation.stop()
            self.land()
        flights = []
        if start == rules.bar_of(player):
            origin = L.bar_center(player, min(before[start][0], BAR_SHOWN) - 1)
            origin_size = L.BAR_CHECKER
        else:
            origin = L.checker_center(start, min(before[start][0], L.MAX_SHOWN) - 1)
            origin_size = L.CHECKER
        if end is None:
            x, y, w, h = L.slab_rect(player, rules.borne_off(after, player) - 1)
            flights.append(Flight(player, origin, (x + w / 2, y + h / 2), origin_size, L.SLAB_H * 2,
                                  ('off', player)))
        else:
            target = L.checker_center(end, min(after[end][0], L.MAX_SHOWN) - 1)
            flights.append(Flight(player, origin, target, origin_size, L.CHECKER, ('point', end)))
            if hit:
                bar = rules.bar_of(-player)
                to_bar = L.bar_center(-player, min(after[bar][0], BAR_SHOWN) - 1)
                flights.append(Flight(-player, L.checker_center(end, 0), to_bar, L.CHECKER, L.BAR_CHECKER,
                                      ('bar', -player)))
        self.flights = flights
        self.flight_board = [cell[:] for cell in after]
        self.progress = 0.0
        self.animation.start()

    def on_progress(self, value):
        self.progress = value
        self.update()

    def land(self):
        self.flights = []
        self.progress = 1.0
        self.update()

    def hidden(self, kind, owner_or_point):
        """How many checkers to leave out at a place because they are still on their way there"""
        return sum(1 for f in self.flights if f.lands_on == (kind, owner_or_point))

    # Keyboard

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self.navigate.emit(-1)
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            self.navigate.emit(1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.activate.emit()
        elif key == Qt.Key.Key_Escape:
            self.cancel.emit()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
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
        self.paint_flights(p)
        if self.hasFocus():
            self.paint_cursor(p)
        p.end()

    def paint_flights(self, p):
        t = self.progress
        for f in self.flights:
            x = f.start[0] + (f.end[0] - f.start[0]) * t
            y = f.start[1] + (f.end[1] - f.start[1]) * t
            size = f.start_size + (f.end_size - f.start_size) * t
            self.paint_checker(p, QPointF(x, y), size, f.owner)

    def paint_cursor(self, p):
        cursor = self.view.cursor
        if cursor is None:
            return
        kind, point = cursor
        if kind == 'point':
            x, y, w, h, _ = L.point_rect(point)
            rect = QRectF(x - 3, y - 3, w + 6, h + 6)
        elif kind == 'bar':
            rect = QRectF(L.BAR_X - 3, L.PAD + 2, L.BAR_W + 6, L.H - 2 * L.PAD - 4)
        else:
            x, y, w, h = L.tray_rect(self.view.player)
            rect = QRectF(x - 3, y - 3, w + 6, h + 6)
        p.setPen(QPen(qcolor('text'), 2, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect, 6, 6)

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
        count -= self.hidden('point', point)
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
            count = self.view.board[bar][0] - self.hidden('bar', player)
            for slot in range(min(count, BAR_SHOWN)):
                is_top = slot == min(count, BAR_SHOWN) - 1
                ring = None
                if is_top and self.view.selected == bar:
                    ring = 'selected'
                elif is_top and bar in self.view.sources and self.view.selected is None:
                    ring = 'movable'
                label = str(count) if is_top and count > BAR_SHOWN else None
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
            for index in range(off - self.hidden('off', player)):
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
