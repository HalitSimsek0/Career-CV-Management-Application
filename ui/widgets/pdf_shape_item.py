from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QMenu, QColorDialog
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor, QBrush, QCursor


class PDFShapeItem(QGraphicsRectItem):
    def __init__(self, shape_type, x, y, width, height, color=(0, 0, 0), fill_color=None, line_width=1.0, parent=None):
        # We define the rectangle boundary from 0,0 to width,height
        super().__init__(0, 0, width, height, parent)
        self.shape_type = shape_type  # "rect" or "ellipse"
        self.setPos(x, y)

        # Pen & Brush properties
        self._color = color
        self._fill_color = fill_color
        self._line_width = line_width
        self.update_style()

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def update_style(self):
        r, g, b = self._color
        pen = QPen(QColor(int(r * 255), int(g * 255), int(b * 255)))
        pen.setWidthF(self._line_width)
        self.setPen(pen)

        if self._fill_color:
            fr, fg, fb = self._fill_color
            brush = QBrush(QColor(int(fr * 255), int(fg * 255), int(fb * 255)))
            self.setBrush(brush)
        else:
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def paint(self, painter, option, widget):
        if self.shape_type == "ellipse":
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawEllipse(self.rect())

            # Draw selection bounding box dashed line if selected
            if self.isSelected():
                painter.setPen(QPen(QColor("#60a5fa"), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
                painter.drawRect(self.rect())
        else:
            # Let standard QGraphicsRectItem paint handle it
            super().paint(painter, option, widget)

    def set_border_color(self, color: QColor):
        self._color = (color.redF(), color.greenF(), color.blueF())
        self.update_style()

    def set_fill_color(self, color: QColor):
        if color.isValid() and color != Qt.GlobalColor.transparent:
            self._fill_color = (color.redF(), color.greenF(), color.blueF())
        else:
            self._fill_color = None
        self.update_style()

    def set_line_width(self, width: float):
        self._line_width = width
        self.update_style()

    def set_dimensions(self, width: float, height: float):
        self.prepareGeometryChange()
        self.setRect(0, 0, width, height)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Sil")
        border_color_action = menu.addAction("Kenarlık Rengi Seç...")
        fill_color_action = menu.addAction("Dolgu Rengi Seç...")
        clear_fill_action = menu.addAction("Dolgu Kaldır")

        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().removeItem(self)
        elif action == border_color_action:
            color = QColorDialog.getColor(QColor(int(self._color[0]*255), int(self._color[1]*255), int(self._color[2]*255)), None, "Kenarlık Rengi Seçin")
            if color.isValid():
                self.set_border_color(color)
        elif action == fill_color_action:
            initial = QColor(255, 255, 255)
            if self._fill_color:
                initial = QColor(int(self._fill_color[0]*255), int(self._fill_color[1]*255), int(self._fill_color[2]*255))
            color = QColorDialog.getColor(initial, None, "Dolgu Rengi Seçin")
            if color.isValid():
                self.set_fill_color(color)
        elif action == clear_fill_action:
            self.set_fill_color(QColor(Qt.GlobalColor.transparent))

    def get_data(self):
        rect = self.rect()
        pos = self.pos()
        return {
            "type": self.shape_type,
            "x": pos.x(),
            "y": pos.y(),
            "width": rect.width(),
            "height": rect.height(),
            "color": self._color,
            "fill_color": self._fill_color,
            "line_width": self._line_width,
        }
