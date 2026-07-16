from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QSpinBox, QColorDialog,
    QDoubleSpinBox, QFrame, QLayout, QDialog, QButtonGroup,
    QRadioButton,
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QColor
from ui.widgets.pdf_canvas_widget import PDFCanvasWidget
from services.pdf_edit_service import PDFEditService


class FlowLayout(QLayout):
    def __init__(self, parent=None, spacing=10):
        super().__init__(parent)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spacing = self.spacing()

        # Group items into rows
        rows = []
        current_row = []

        for item in self.itemList:
            item_w = item.sizeHint().width()
            item_h = item.sizeHint().height()

            # Check if this item overflows the layout boundary
            if x + item_w > rect.x() + rect.width() and len(current_row) > 0:
                rows.append((current_row, lineHeight))
                current_row = []
                x = rect.x()
                lineHeight = 0

            current_row.append(item)
            lineHeight = max(lineHeight, item_h)
            x += item_w + spacing

        if current_row:
            rows.append((current_row, lineHeight))

        # Position items row-by-row
        curr_y = rect.y()
        for row_items, lh in rows:
            curr_x = rect.x()
            for item in row_items:
                if not testOnly:
                    # Center vertically in the row
                    offset_y = (lh - item.sizeHint().height()) // 2
                    item.setGeometry(QRect(QPoint(curr_x, curr_y + offset_y), item.sizeHint()))
                curr_x += item.sizeHint().width() + spacing
            curr_y += lh + spacing

        return curr_y - rect.y()


BASIC_FONTS = [
    "Arial", "Times New Roman", "Courier New", "Verdana",
    "Georgia", "Tahoma", "Trebuchet MS", "Calibri",
    "Segoe UI", "Helvetica", "Palatino", "Garamond",
]





class PDFEditorPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = PDFEditService()
        self._pages_data = []
        self._file_path = ""
        self._updating_toolbar = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Header Panel (Navbar Container) ---
        header_panel = QFrame()
        header_panel.setObjectName("pdfHeaderPanel")
        header_panel.setStyleSheet("""
            QFrame#pdfHeaderPanel {
                background-color: rgba(255, 255, 255, 120);
                border-bottom: 1px solid rgba(255, 255, 255, 200);
            }
        """)
        header_layout = QVBoxLayout(header_panel)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        # --- Toolbar 1: File operations ---
        toolbar = QWidget()
        toolbar.setFixedHeight(52)
        toolbar.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 12);
                color: #c7d2fe;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 4px 12px;
                min-height: 32px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(244, 114, 182, 25);
                border-color: rgba(244, 114, 182, 50);
                color: #fbcfe8;
            }
            QPushButton#primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #f9a8d4);
                color: white;
                border: none;
            }
            QPushButton#primaryBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #7c3aed);
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 10, 16, 10)
        toolbar_layout.setSpacing(8)
        toolbar_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("PDF Düzenleyici")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #60a5fa; background: transparent; padding-right: 4px;")
        toolbar_layout.addWidget(title)
        
        self._add_separator(toolbar_layout)

        # Page Navigation controls
        prev_page_btn = QPushButton("◀")
        prev_page_btn.setFixedSize(32, 32)
        prev_page_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 12px; border-radius: 12px; color: #8b5cf6;")
        prev_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_page_btn.setToolTip("Önceki Sayfa")
        prev_page_btn.clicked.connect(self._prev_page)
        toolbar_layout.addWidget(prev_page_btn)

        self._page_label = QLabel("Sayfa: 0 / 0")
        self._page_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #c4b5fd; padding: 0 4px;")
        toolbar_layout.addWidget(self._page_label)

        next_page_btn = QPushButton("▶")
        next_page_btn.setFixedSize(32, 32)
        next_page_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 12px; border-radius: 12px; color: #8b5cf6;")
        next_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_page_btn.setToolTip("Sonraki Sayfa")
        next_page_btn.clicked.connect(self._next_page)
        toolbar_layout.addWidget(next_page_btn)

        toolbar_layout.addStretch()

        open_btn = QPushButton("PDF Aç")
        open_btn.setObjectName("primaryBtn")
        open_btn.setMinimumWidth(100)
        open_btn.setFixedHeight(32)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(self._open_file)
        toolbar_layout.addWidget(open_btn)

        save_btn = QPushButton("Farklı Kaydet")
        save_btn.setObjectName("primaryBtn")
        save_btn.setMinimumWidth(110)
        save_btn.setFixedHeight(32)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_file)
        toolbar_layout.addWidget(save_btn)

        self._add_separator(toolbar_layout)

        # Undo / Redo controls
        self._undo_btn = QPushButton("↶")
        self._undo_btn.setFixedSize(32, 32)
        self._undo_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 15px; border-radius: 12px; color: #8b5cf6;")
        self._undo_btn.setToolTip("Geri Al")
        self._undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._undo_btn.clicked.connect(self._undo)
        toolbar_layout.addWidget(self._undo_btn)

        self._redo_btn = QPushButton("↷")
        self._redo_btn.setFixedSize(32, 32)
        self._redo_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 15px; border-radius: 12px; color: #8b5cf6;")
        self._redo_btn.setToolTip("İleri Al")
        self._redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._redo_btn.clicked.connect(self._redo)
        toolbar_layout.addWidget(self._redo_btn)

        self._add_separator(toolbar_layout)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(32, 32)
        zoom_in_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 15px; border-radius: 12px; color: #8b5cf6;")
        zoom_in_btn.setToolTip("Yakınlaş")
        zoom_in_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedSize(32, 32)
        zoom_out_btn.setStyleSheet("padding: 0px; font-weight: bold; font-size: 15px; border-radius: 12px; color: #8b5cf6;")
        zoom_out_btn.setToolTip("Uzaklaş")
        zoom_out_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)

        fit_btn = QPushButton("Sığdır")
        fit_btn.setFixedSize(60, 32)
        fit_btn.setStyleSheet("padding: 0px; font-size: 12px; border-radius: 12px; color: #8b5cf6;")
        fit_btn.setToolTip("Ekrana Sığdır")
        fit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fit_btn.clicked.connect(self._zoom_reset)
        toolbar_layout.addWidget(fit_btn)

        header_layout.addWidget(toolbar)

        # --- Toolbar 2: Editing tools ---
        toolbar2 = QWidget()
        toolbar2.setObjectName("pdfEditingToolbar")
        toolbar2.setMinimumHeight(48)
        toolbar2.setStyleSheet("""
            QWidget#pdfEditingToolbar {
                background-color: rgba(255, 255, 255, 100);
                border: none;
                border-top: 1px solid rgba(255, 255, 255, 180);
                border-bottom: 1px solid rgba(255, 255, 255, 180);
            }
        """)
        toolbar2_layout = QHBoxLayout(toolbar2)
        toolbar2_layout.setContentsMargins(16, 8, 16, 8)
        toolbar2_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 12);
                color: #c7d2fe;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 4px 12px;
                min-height: 32px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(244, 114, 182, 25);
                border-color: rgba(244, 114, 182, 50);
                color: #fbcfe8;
            }
        """

        # Page management
        add_page_btn = QPushButton("+ Sayfa")
        add_page_btn.setStyleSheet(btn_style)
        add_page_btn.setFixedHeight(32)
        add_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_page_btn.clicked.connect(self._add_page)
        toolbar2_layout.addWidget(add_page_btn)

        del_page_btn = QPushButton("− Sayfa")
        del_page_btn.setStyleSheet(btn_style)
        del_page_btn.setFixedHeight(32)
        del_page_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_page_btn.clicked.connect(self._delete_page)
        toolbar2_layout.addWidget(del_page_btn)

        self._add_separator(toolbar2_layout)

        # Add elements
        add_text_btn = QPushButton("Metin")
        add_text_btn.setStyleSheet(btn_style)
        add_text_btn.setFixedHeight(32)
        add_text_btn.setToolTip("Metin Ekle")
        add_text_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_text_btn.clicked.connect(self._add_text)
        toolbar2_layout.addWidget(add_text_btn)

        add_line_btn = QPushButton("Çizgi")
        add_line_btn.setStyleSheet(btn_style)
        add_line_btn.setFixedHeight(32)
        add_line_btn.setToolTip("Çizgi Ekle")
        add_line_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_line_btn.clicked.connect(self._add_line)
        toolbar2_layout.addWidget(add_line_btn)

        add_image_btn = QPushButton("Resim")
        add_image_btn.setStyleSheet(btn_style)
        add_image_btn.setFixedHeight(32)
        add_image_btn.setToolTip("Resim Ekle")
        add_image_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_image_btn.clicked.connect(self._add_image)
        toolbar2_layout.addWidget(add_image_btn)

        self._add_separator(toolbar2_layout)

        # Font controls
        self._font_combo = QComboBox()
        self._font_combo.addItems(BASIC_FONTS)
        self._font_combo.setMinimumWidth(80)
        self._font_combo.setFixedHeight(32)
        self._font_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._font_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 10);
                color: #8b5cf6;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 2px 24px 2px 8px;
                min-height: 32px;
            }
            QComboBox:hover {
                border-color: rgba(244, 114, 182, 50);
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #c4b5fd;
                margin-right: 6px;
            }
        """)
        self._font_combo.currentTextChanged.connect(self._change_font)
        toolbar2_layout.addWidget(self._font_combo)

        spin_style = """
            QSpinBox, QDoubleSpinBox {
                background-color: rgba(255, 255, 255, 10);
                color: #8b5cf6;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                min-height: 32px;
            }
            QSpinBox::hover, QDoubleSpinBox::hover {
                border-color: rgba(244, 114, 182, 50);
            }
            QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {
                padding: 0px 18px 0px 4px;
                border: none;
                background: transparent;
                color: #8b5cf6;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid rgba(255, 255, 255, 15);
                border-bottom: 1px solid rgba(255, 255, 255, 15);
                background-color: rgba(255, 255, 255, 8);
                border-top-right-radius: 7px;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: rgba(244, 114, 182, 20);
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid rgba(255, 255, 255, 15);
                background-color: rgba(255, 255, 255, 8);
                border-bottom-right-radius: 7px;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: rgba(244, 114, 182, 20);
            }
        """

        self._size_spin = QSpinBox()
        self._size_spin.setRange(6, 72)
        self._size_spin.setValue(12)
        self._size_spin.setMinimumWidth(50)
        self._size_spin.setFixedHeight(32)
        self._size_spin.setSuffix("pt")
        self._size_spin.setStyleSheet(spin_style)
        self._size_spin.valueChanged.connect(self._change_size)
        toolbar2_layout.addWidget(self._size_spin)

        format_btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 12);
                color: #c7d2fe;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 0px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(244, 114, 182, 25);
                border-color: rgba(244, 114, 182, 50);
                color: #fbcfe8;
            }
        """

        self._align_combo = QComboBox()
        self._align_combo.addItems(["Hizala...", "Sola Hizala", "Ortala", "Sağa Hizala"])
        self._align_combo.setMinimumWidth(80)
        self._align_combo.setFixedHeight(32)
        self._align_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._align_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 10);
                color: #8b5cf6;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 2px 20px 2px 6px;
                min-height: 32px;
            }
            QComboBox:hover {
                border-color: rgba(244, 114, 182, 50);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #c4b5fd;
                margin-right: 4px;
            }
        """)
        self._align_combo.currentTextChanged.connect(self._change_alignment)
        toolbar2_layout.addWidget(self._align_combo)
 

        bold_btn = QPushButton("B")
        bold_btn.setFixedSize(32, 32)
        bold_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bold_btn.setStyleSheet(format_btn_style + " QPushButton { font-weight: bold; }")
        bold_btn.setToolTip("Kalın")
        bold_btn.clicked.connect(self._toggle_bold)
        toolbar2_layout.addWidget(bold_btn)

        italic_btn = QPushButton("I")
        italic_btn.setFixedSize(32, 32)
        italic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        italic_btn.setStyleSheet(format_btn_style + " QPushButton { font-style: italic; }")
        italic_btn.setToolTip("İtalik")
        italic_btn.clicked.connect(self._toggle_italic)
        toolbar2_layout.addWidget(italic_btn)

        underline_btn = QPushButton("U")
        underline_btn.setFixedSize(32, 32)
        underline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        underline_btn.setStyleSheet(format_btn_style + " QPushButton { font-weight: bold; text-decoration: underline; }")
        underline_btn.setToolTip("Altı Çizili")
        underline_btn.clicked.connect(self._toggle_underline)
        toolbar2_layout.addWidget(underline_btn)

        strike_btn = QPushButton("S")
        strike_btn.setFixedSize(32, 32)
        strike_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        strike_btn.setStyleSheet(format_btn_style + " QPushButton { font-weight: bold; text-decoration: line-through; }")
        strike_btn.setToolTip("Üstü Çizili")
        strike_btn.clicked.connect(self._toggle_strikeout)
        toolbar2_layout.addWidget(strike_btn)

        # Color
        self._color_btn = QPushButton("🎨")
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_btn.setStyleSheet(format_btn_style)
        self._color_btn.setToolTip("Yazı Rengi")
        self._color_btn.clicked.connect(self._change_color)
        toolbar2_layout.addWidget(self._color_btn)

        self._add_separator(toolbar2_layout)

        # Line controls
        lbl_lw = QLabel("Çizgi:")
        lbl_lw.setStyleSheet("background: transparent; font-size: 12px; font-weight: 600; color: #8b5cf6; margin: 0px 4px;")
        toolbar2_layout.addWidget(lbl_lw)

        self._line_width_spin = QDoubleSpinBox()
        self._line_width_spin.setRange(0.5, 10.0)
        self._line_width_spin.setValue(1.0)
        self._line_width_spin.setSingleStep(0.5)
        self._line_width_spin.setMinimumWidth(55)
        self._line_width_spin.setFixedHeight(32)
        self._line_width_spin.setStyleSheet(spin_style)
        self._line_width_spin.setToolTip("Çizgi Kalınlığı")
        self._line_width_spin.valueChanged.connect(self._change_line_width)
        toolbar2_layout.addWidget(self._line_width_spin)

        self._line_len_spin = QSpinBox()
        self._line_len_spin.setRange(10, 2000)
        self._line_len_spin.setValue(200)
        self._line_len_spin.setSingleStep(10)
        self._line_len_spin.setMinimumWidth(60)
        self._line_len_spin.setFixedHeight(32)
        self._line_len_spin.setStyleSheet(spin_style)
        self._line_len_spin.setToolTip("Çizgi Uzunluğu")
        self._line_len_spin.valueChanged.connect(self._change_line_length)
        toolbar2_layout.addWidget(self._line_len_spin)

        self._add_separator(toolbar2_layout)

        toolbar2_layout.addStretch()

        self._crop_btn = QPushButton("Kes")
        self._crop_btn.setFixedHeight(32)
        self._crop_btn.setFixedWidth(60)
        self._crop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._crop_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 12);
                color: #c7d2fe;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 12px;
                padding: 2px 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(244, 114, 182, 25);
                border-color: rgba(244, 114, 182, 50);
                color: #fbcfe8;
            }
        """)
        self._crop_btn.setToolTip("Seçili Resmi Kes")
        self._crop_btn.clicked.connect(self._crop_selected)
        self._crop_btn.setVisible(False)
        toolbar2_layout.addWidget(self._crop_btn)

        del_item_btn = QPushButton("Sil")
        del_item_btn.setFixedHeight(32)
        del_item_btn.setFixedWidth(60)
        del_item_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_item_btn.setObjectName("dangerBtn")
        del_item_btn.setStyleSheet("padding: 2px 4px; font-size: 11px;")
        del_item_btn.setToolTip("Seçili Öğeyi Sil")
        del_item_btn.clicked.connect(self._delete_selected)
        toolbar2_layout.addWidget(del_item_btn)

        header_layout.addWidget(toolbar2)

        layout.addWidget(header_panel)

        # --- Spacer between toolbar and canvas ---
        spacer = QWidget()
        spacer.setFixedHeight(16)
        spacer.setStyleSheet("background-color: transparent;")
        layout.addWidget(spacer)

        # --- Canvas ---
        self._canvas_container = QWidget()
        self._canvas_container.setStyleSheet("background-color: transparent;")
        canvas_layout = QVBoxLayout(self._canvas_container)
        canvas_layout.setContentsMargins(16, 0, 16, 16)

        self._canvas = PDFCanvasWidget()
        self._canvas.setStyleSheet("border: 1px solid rgba(255, 255, 255, 200); border-radius: 12px; background-color: #faf5ff;")
        self._canvas.hide()
        self._canvas.selection_changed.connect(self._on_canvas_selection_changed)
        self._canvas.page_changed.connect(self._on_page_changed)
        canvas_layout.addWidget(self._canvas, 1)

        self._empty_overlay = QWidget()
        overlay_layout = QVBoxLayout(self._empty_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        msg = QLabel("PDF dosyası yüklemek için\naşağıdaki butona tıklayın")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setStyleSheet("color: #a78bfa; font-size: 16px; margin-bottom: 20px;")
        overlay_layout.addWidget(msg)

        big_open_btn = QPushButton("PDF Dosyası Aç")
        big_open_btn.setObjectName("primaryBtn")
        big_open_btn.setFixedSize(200, 50)
        big_open_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(244, 114, 182, 20);
                color: #fbcfe8;
                border: 1px solid rgba(244, 114, 182, 40);
                font-size: 16px; font-weight: bold; border-radius: 25px;
            }
            QPushButton:hover {
                background-color: rgba(244, 114, 182, 40);
            }
        """)
        big_open_btn.clicked.connect(self._open_file)
        overlay_layout.addWidget(big_open_btn, 0, Qt.AlignmentFlag.AlignHCenter)

        canvas_layout.addWidget(self._empty_overlay)

        layout.addWidget(self._canvas_container, 1)

        self._status = QLabel("")
        self._status.setFixedHeight(24)
        self._status.setStyleSheet("""
            QLabel {
                color: #8b5cf6;
                padding: 2px 16px;
                font-size: 11px;
                background-color: rgba(255, 255, 255, 150);
                border-top: 1px solid rgba(255, 255, 255, 200);
            }
        """)
        layout.addWidget(self._status)

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setFixedWidth(1)
        sep.setFixedHeight(20)
        sep.setStyleSheet("background-color: #c7d2fe; border: none; margin: 0px 8px;")
        layout.addWidget(sep)

    def _on_canvas_selection_changed(self):
        """When an item is selected on canvas, update toolbar to reflect its properties"""
        if self._updating_toolbar:
            return
        self._updating_toolbar = True
        try:
            self._crop_btn.setVisible(False)
            
            text_item = self._canvas.get_selected_text_item()
            if text_item:
                font = text_item.font()
                family = font.family()
                idx = self._font_combo.findText(family)
                if idx >= 0:
                    self._font_combo.setCurrentIndex(idx)
                size = font.pixelSize()
                if size > 0:
                    self._size_spin.setValue(size)

            line_item = self._canvas.get_selected_line_item()
            if line_item:
                self._line_width_spin.setValue(line_item.pen().widthF())
                line = line_item.line()
                length = abs(line.x2() - line.x1())
                if length > 0:
                    self._line_len_spin.setValue(int(length))
                    
            image_item = self._canvas.get_selected_image_item()
            if image_item:
                self._crop_btn.setVisible(True)
                
        finally:
            self._updating_toolbar = False

    def load_pdf(self, file_path: str):
        try:
            self._file_path = file_path
            self._service.close()
            self._pages_data = self._service.open_pdf(file_path)
            self._canvas.load_pages(self._pages_data)
            self._empty_overlay.hide()
            self._canvas.show()
            page_count = len(self._pages_data)
            self._page_label.setText(f"Sayfa: 1 / {page_count}")
            self._status.setText(f"Yüklendi: {file_path}  |  {page_count} sayfa  |  Çift tık: metin düzenle  •  Sürükle: taşı  •  Ctrl+Z: geri al")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF açılamadı:\n{str(e)}")

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "PDF Dosyası Seç", "", "PDF (*.pdf)"
        )
        if file_path:
            self.load_pdf(file_path)

    def _save_file(self):
        if not self._pages_data:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek PDF yok. Önce bir PDF açın.")
            return
        output, _ = QFileDialog.getSaveFileName(
            self, "PDF Kaydet", "", "PDF (*.pdf)"
        )
        if not output:
            return
        try:
            modified = self._canvas.get_all_elements(self._pages_data)
            self._service.save_pdf(output, modified)
            self._status.setText(f"Kaydedildi: {output}")
            QMessageBox.information(self, "Başarılı", f"PDF kaydedildi:\n{output}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF kaydedilemedi:\n{str(e)}")

    def _zoom_in(self):
        self._canvas.zoom_in()

    def _zoom_out(self):
        self._canvas.zoom_out()

    def _zoom_reset(self):
        self._canvas.zoom_reset()

    def _add_text(self):
        self._canvas.add_new_text()

    def _add_line(self):
        self._canvas.add_new_line()

    def _delete_selected(self):
        self._canvas.delete_selected()

    def _crop_selected(self):
        self._canvas.crop_selected_image()

    def _toggle_bold(self):
        self._canvas.toggle_bold()

    def _toggle_italic(self):
        self._canvas.toggle_italic()
        
    def _toggle_underline(self):
        self._canvas.toggle_underline()

    def _toggle_strikeout(self):
        self._canvas.toggle_strikeout()

    def _change_alignment(self, alignment):
        if alignment == "Hizala...":
            return
        if self._updating_toolbar:
            return
        self._canvas.change_alignment(alignment)
        
        self._updating_toolbar = True
        try:
            self._align_combo.setCurrentIndex(0)
        finally:
            self._updating_toolbar = False
        
    def _change_font(self, font_name):
        if self._updating_toolbar:
            return
        self._canvas.change_font(font_name)
        
    def _change_size(self, size):
        if self._updating_toolbar:
            return
        self._canvas.change_font_size(size)

    def _change_color(self):
        color = QColorDialog.getColor(QColor(0, 0, 0), self, "Yazı Rengi Seçin")
        if color.isValid():
            self._canvas.change_border_color(color)

    def _change_line_width(self, width):
        if self._updating_toolbar:
            return
        self._canvas.change_line_width(width)

    def _change_line_length(self, length):
        if self._updating_toolbar:
            return
        self._canvas.change_line_length(float(length))
        
    def _add_page(self):
        if not self._pages_data:
            return
        self._canvas.add_new_page()
        from services.pdf_edit_service import PageData
        self._pages_data.append(PageData(width=self._pages_data[0].width, height=self._pages_data[0].height))
        self._page_label.setText(f"Sayfa: {len(self._pages_data)} / {len(self._pages_data)}")
        self._status.setText(f"Yeni sayfa eklendi. Toplam: {len(self._pages_data)}")
        
    def _delete_page(self):
        if not self._pages_data:
            return
        if len(self._pages_data) <= 1:
            QMessageBox.warning(self, "Uyarı", "Son sayfayı silemezsiniz.")
            return
        self._canvas.delete_last_page()
        self._pages_data.pop()
        current_visible = min(self._canvas._current_page + 1, len(self._pages_data))
        self._page_label.setText(f"Sayfa: {current_visible} / {len(self._pages_data)}")
        self._status.setText(f"Son sayfa silindi. Toplam: {len(self._pages_data)}")

    def _add_image(self):
        if not self._pages_data:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Resim Seç", "", "Resimler (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    img_bytes = f.read()
                self._canvas.add_new_image(img_bytes)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Resim yüklenemedi:\n{str(e)}")

    def _undo(self):
        self._canvas.undo()

    def _redo(self):
        self._canvas.redo()

    def _prev_page(self):
        if self._pages_data and self._canvas._current_page > 0:
            self._canvas.go_to_page(self._canvas._current_page - 1)

    def _next_page(self):
        if self._pages_data and self._canvas._current_page < len(self._pages_data) - 1:
            self._canvas.go_to_page(self._canvas._current_page + 1)

    def _on_page_changed(self, page_idx):
        if self._pages_data:
            self._page_label.setText(f"Sayfa: {page_idx + 1} / {len(self._pages_data)}")

