from PyQt6.QtWidgets import (
    QGraphicsTextItem, QGraphicsItem, QMenu, QColorDialog,
)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QFont, QColor, QCursor, QTextCursor, QBrush


class PDFTextBlockItem(QGraphicsTextItem):
    def __init__(self, text, x, y, font_size, font_name, color, block_id, parent=None):
        super().__init__(parent)
        self.block_id = block_id
        self._editing = False
        self._original_text = text
        self._bg_color = None

        self.setPlainText(text)
        self.setPos(x, y)
        self.setDefaultTextColor(QColor(int(color[0]*255), int(color[1]*255), int(color[2]*255)))

        font = QFont()
        # PDF font size is in points. Use pixel size for correct canvas positioning.
        # PDF coordinate: 1 pt = 1 unit. Screen renders at ~96 DPI so 1 pt ≈ 1.33 px.
        # Using setPixelSize ensures text matches PDF layout coordinates.
        pixel_size = max(1, int(font_size))
        font.setPixelSize(pixel_size)
        if "bold" in font_name.lower():
            font.setBold(True)
        if "italic" in font_name.lower():
            font.setItalic(True)
        self.setFont(font)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))

    def mouseDoubleClickEvent(self, event):
        self._editing = True
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.setFocus()
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.setTextCursor(cursor)
        super().mouseDoubleClickEvent(event)

    def focusOutEvent(self, event):
        if self._editing:
            self._editing = False
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._editing = False
            self.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            self.clearFocus()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = menu.addAction("Sil")
        reset_action = menu.addAction("Sıfırla")
        font_up = menu.addAction("Yazı Büyüt")
        font_down = menu.addAction("Yazı Küçült")
        bold_action = menu.addAction("Kalın")
        highlight_action = menu.addAction("Vurgu Rengi Seç...")
        clear_highlight = menu.addAction("Vurguyu Kaldır")
        action = menu.exec(event.screenPos())
        if action == delete_action:
            self.scene().removeItem(self)
        elif action == reset_action:
            self.setPlainText(self._original_text)
        elif action == font_up:
            f = self.font()
            f.setPixelSize(f.pixelSize() + 1)
            self.setFont(f)
        elif action == font_down:
            f = self.font()
            if f.pixelSize() > 4:
                f.setPixelSize(f.pixelSize() - 1)
                self.setFont(f)
        elif action == bold_action:
            f = self.font()
            f.setBold(not f.bold())
            self.setFont(f)
        elif action == highlight_action:
            initial = QColor(255, 255, 0)
            if self._bg_color:
                initial = self._bg_color
            color = QColorDialog.getColor(initial, None, "Vurgu Rengi Seçin")
            if color.isValid():
                self.set_background_color(color)
        elif action == clear_highlight:
            self.set_background_color(QColor(Qt.GlobalColor.transparent))

    def setDefaultTextColor(self, color: QColor):
        super().setDefaultTextColor(color)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        char_format = cursor.charFormat()
        char_format.setForeground(color)
        cursor.setCharFormat(char_format)
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def set_background_color(self, color: QColor):
        if color.isValid() and color != Qt.GlobalColor.transparent:
            self._bg_color = color
            brush = QBrush(color)
        else:
            self._bg_color = None
            brush = QBrush(Qt.GlobalColor.transparent)
        
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        char_format = cursor.charFormat()
        char_format.setBackground(brush)
        cursor.setCharFormat(char_format)
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def set_alignment(self, alignment: Qt.AlignmentFlag):
        doc = self.document()
        opt = doc.defaultTextOption()
        opt.setAlignment(alignment)
        doc.setDefaultTextOption(opt)

        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        block_format = cursor.blockFormat()
        block_format.setAlignment(alignment)
        cursor.setBlockFormat(block_format)
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def get_data(self):
        font = self.font()
        styles = []
        if font.bold():
            styles.append("bold")
        if font.italic():
            styles.append("italic")
        styles_str = "|".join(styles) if styles else "normal"

        bg_color_val = None
        if hasattr(self, "_bg_color") and self._bg_color is not None:
            bg_color_val = (self._bg_color.redF(), self._bg_color.greenF(), self._bg_color.blueF())

        align_flag = self.document().defaultTextOption().alignment()
        if align_flag & Qt.AlignmentFlag.AlignHCenter:
            align_val = 1
        elif align_flag & Qt.AlignmentFlag.AlignRight:
            align_val = 2
        else:
            align_val = 0

        return {
            "text": self.toPlainText(),
            "x": self.pos().x(),
            "y": self.pos().y(),
            "width": self.boundingRect().width(),
            "height": self.boundingRect().height(),
            "font_size": font.pixelSize(),
            "font_name": styles_str,
            "color": (
                self.defaultTextColor().redF(),
                self.defaultTextColor().greenF(),
                self.defaultTextColor().blueF(),
            ),
            "block_id": self.block_id,
            "bg_color": bg_color_val,
            "align": align_val,
        }
