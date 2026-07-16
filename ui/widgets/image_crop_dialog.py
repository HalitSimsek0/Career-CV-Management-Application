from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QRubberBand, QScrollArea, QWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QPixmap, QImage, QPainter

class CropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.origin = QPoint()
        self.current_rect = QRect()
        self.is_cropping = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            self.is_cropping = True

    def mouseMoveEvent(self, event):
        if self.is_cropping:
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_cropping = False
            self.current_rect = self.rubber_band.geometry()

    def get_cropped_rect(self) -> QRect:
        return self.current_rect


class ImageCropDialog(QDialog):
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Resmi Kes")
        self.setMinimumSize(600, 500)
        
        self.original_pixmap = pixmap
        self.cropped_pixmap = None
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("Kesmek istediğiniz alanı fareyle sürükleyerek seçin:")
        info_label.setStyleSheet("color: #60a5fa; font-size: 14px; font-weight: bold;")
        layout.addWidget(info_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        
        self.image_label = CropLabel()
        self.image_label.setPixmap(self.original_pixmap)
        self.image_label.resize(self.original_pixmap.size())
        
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.scroll_area)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        crop_btn = QPushButton("Kes ve Uygula")
        crop_btn.setObjectName("primaryBtn")
        crop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        crop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #f9a8d4);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:1 #7c3aed);
            }
        """)
        crop_btn.clicked.connect(self._apply_crop)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(crop_btn)

        layout.addLayout(btn_layout)

    def _apply_crop(self):
        rect = self.image_label.get_cropped_rect()
        if rect.isValid() and rect.width() > 0 and rect.height() > 0:
            self.cropped_pixmap = self.original_pixmap.copy(rect)
            self.accept()
        else:
            self.reject()

    def get_cropped_pixmap(self) -> QPixmap:
        return self.cropped_pixmap
