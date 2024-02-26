from PyQt6.QtCore import pyqtSignal, QPointF, QObject
from PyQt6.QtGui import QPainter, QColor, QPolygonF, QPen
from PyQt6.QtWidgets import QGraphicsEllipseItem, QStyleOptionGraphicsItem, QWidget, QGraphicsPolygonItem, \
    QGraphicsRectItem


class Clickable:
    def __init__(self):
        self.clicked = communication()
        self.clicked.point_item = self


class Colable(Clickable):
    def __init__(self, col):
        super().__init__()
        self.col = col


class PointItem(QGraphicsEllipseItem, Colable):
    s = pyqtSignal()

    def __init__(self, x, y, radius, player, col):
        super().__init__(x, y, radius * 2, radius * 2, col=None)
        Colable.__init__(self, col)
        self.player = player
        self.color = "white" if player == 1 else "black"
        self.outline = "black" if player == 1 else "white"
        self.setPos(x, y)
        self.setAcceptHoverEvents(True)
        self.setEnabled(False)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        painter.setBrush(QColor(self.color))
        pen = QPen(QColor(self.outline))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(self.rect())

    def is_marked(self, flag):
        if not flag:
            self.outline = "black" if self.player == 1 else "white"
        else:
            self.outline = ("skyblue"
                            "")
        self.update()

    def mousePressEvent(self, event):
        if self.contains(event.pos()):
            self.clicked.communicate.emit()
        self.setOpacity(1.0)
        super(PointItem, self).mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setOpacity(0.7)  # Change opacity on hover for better feedback
        super(PointItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(1.0)  # Restore opacity when not hovering
        super(PointItem, self).hoverLeaveEvent(event)


class TriangleItem(QGraphicsPolygonItem, Colable):
    s = pyqtSignal()

    def __init__(self, col, x, y, height, width, color, direction):
        triangle_up = QPolygonF([
            QPointF(x, y - height),
            QPointF(x + (width / 2), y),
            QPointF(x - (width / 2), y)
        ])
        triangle_down = QPolygonF([
            QPointF(x, y + height),
            QPointF(x + (width / 2), y),
            QPointF(x - (width / 2), y)
        ])
        triangle = triangle_up if direction == "up" else triangle_down
        super().__init__(triangle, col=None)
        Colable.__init__(self, col)
        self.outline = color
        self.color = color
        self.setEnabled(False)
        self.setAcceptHoverEvents(True)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        painter.setBrush(QColor(self.color))
        pen = QPen(QColor(self.outline))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPolygon(self.polygon())

    def is_marked(self, flag):
        if not flag:
            self.outline = self.color
        else:
            self.outline = "skyblue"
        self.update()

    def mousePressEvent(self, event):
        if self.contains(event.pos()) and not self.is_point_item_under_cursor(event):
            self.clicked.communicate.emit()
        self.setOpacity(1.0)
        super(TriangleItem, self).mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setOpacity(0.7)  # Change opacity on hover for better feedback
        super(TriangleItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(1.0)  # Restore opacity when not hovering
        super(TriangleItem, self).hoverLeaveEvent(event)

    def is_point_item_under_cursor(self, event):
        items = self.scene().items(self.mapToScene(event.pos()))
        for item in items:
            if isinstance(item, PointItem):
                return True
        return False


class throwing_rectangle(QGraphicsRectItem, Colable):
    def __init__(self, col, x, y, width, height):
        super().__init__(x, y, width, height, col=None)
        Colable.__init__(self, col)
        self.setEnabled(True)
        self.setAcceptHoverEvents(True)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        painter.setBrush(QColor("brown"))
        painter.setPen(QColor("black"))
        painter.drawRect(self.rect())

    def mousePressEvent(self, event):
        self.clicked.communicate.emit()
        self.setOpacity(1.0)
        super(throwing_rectangle, self).mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setOpacity(0.7)  # Change opacity on hover for better feedback
        super(throwing_rectangle, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(1.0)  # Restore opacity when not hovering
        super(throwing_rectangle, self).hoverLeaveEvent(event)


class communication(QObject):
    communicate = pyqtSignal()
    point_item = None
