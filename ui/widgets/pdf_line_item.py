from PyQt6.QtWidgets import QGraphicsLineItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QPen, QColor, QCursor


class PDFLineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, color=(0,0,0), width=1.0, parent=None):
        super().__init__(x1, y1, x2, y2, parent)
        r, g, b = color if isinstance(color, tuple) and len(color) == 3 else (0, 0, 0)
        pen = QPen(QColor(int(r*255), int(g*255), int(b*255)))
        pen.setWidthF(width)
        self.setPen(pen)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Sil")
        thicker = menu.addAction("Kalınlaştır")
        thinner = menu.addAction("İncelt")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().removeItem(self)
        elif action == thicker:
            p = self.pen()
            p.setWidthF(p.widthF() + 0.5)
            self.setPen(p)
        elif action == thinner:
            p = self.pen()
            if p.widthF() > 0.5:
                p.setWidthF(p.widthF() - 0.5)
                self.setPen(p)

    def get_data(self):
        line = self.line()
        pos = self.pos()
        return {
            "x1": line.x1() + pos.x(),
            "y1": line.y1() + pos.y(),
            "x2": line.x2() + pos.x(),
            "y2": line.y2() + pos.y(),
            "color": (
                self.pen().color().redF(),
                self.pen().color().greenF(),
                self.pen().color().blueF(),
            ),
            "width": self.pen().widthF(),
        }
