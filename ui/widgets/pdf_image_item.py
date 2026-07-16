from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, QRectF, QRect
from PyQt6.QtGui import QPixmap, QImage, QCursor
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice


class PDFImageItem(QGraphicsPixmapItem):
    def __init__(self, x, y, width, height, image_data, parent=None):
        super().__init__(parent)
        self._image_data = image_data
        self._target_width = width
        self._target_height = height

        img = QImage()
        img.loadFromData(image_data)
        if not img.isNull():
            pixmap = QPixmap.fromImage(img)
            pixmap = pixmap.scaled(
                int(width), int(height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pixmap)

        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Sil")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().removeItem(self)

    def crop_to_rect(self, rect_local: QRectF):
        img = QImage()
        img.loadFromData(self._image_data)
        if img.isNull():
            return
            
        orig_w = img.width()
        orig_h = img.height()
        
        scale_x = orig_w / self._target_width
        scale_y = orig_h / self._target_height
        
        crop_x = int(rect_local.x() * scale_x)
        crop_y = int(rect_local.y() * scale_y)
        crop_w = int(rect_local.width() * scale_x)
        crop_h = int(rect_local.height() * scale_y)
        
        orig_rect = QRect(crop_x, crop_y, crop_w, crop_h).intersected(img.rect())
        if orig_rect.width() <= 0 or orig_rect.height() <= 0:
            return
            
        img = img.convertToFormat(QImage.Format.Format_RGB32)
        from PyQt6.QtGui import QPainter
        from PyQt6.QtCore import Qt
        painter = QPainter(img)
        painter.fillRect(orig_rect, Qt.GlobalColor.white)
        painter.end()
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buffer, "JPEG", quality=85)
        
        self._image_data = byte_array.data()
        
        # Keep visual bounding box stable, no need to change pos or dimensions
        self.set_dimensions(self._target_width, self._target_height)

    def set_dimensions(self, width: float, height: float):
        self.prepareGeometryChange()
        self._target_width = width
        self._target_height = height
        img = QImage()
        img.loadFromData(self._image_data)
        if not img.isNull():
            pixmap = QPixmap.fromImage(img)
            pixmap = pixmap.scaled(
                int(width), int(height),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setPixmap(pixmap)

    def get_data(self):
        return {
            "x": self.pos().x(),
            "y": self.pos().y(),
            "width": self._target_width,
            "height": self._target_height,
            "image_data": self._image_data,
        }
