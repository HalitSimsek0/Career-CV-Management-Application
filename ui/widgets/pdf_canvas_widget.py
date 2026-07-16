from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, QInputDialog, QColorDialog,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QBrush, QFont, QWheelEvent, QPainter, QImage
from ui.widgets.pdf_text_block_item import PDFTextBlockItem
from ui.widgets.pdf_line_item import PDFLineItem
from ui.widgets.pdf_image_item import PDFImageItem
from ui.widgets.pdf_shape_item import PDFShapeItem
from services.pdf_edit_service import PageData, TextBlock, LineElement, ImageElement, ShapeElement


SNAP_THRESHOLD = 4


class PDFCanvasWidget(QGraphicsView):
    selection_changed = pyqtSignal()
    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor("#2a2a4a")))
        self._zoom = 1.0
        self._page_rects = []
        self._current_page = 0
        self._page_gap = 20
        self._undo_stack = []
        self._redo_stack = []
        self._guide_lines = []
        
        self._crop_mode = False
        self._target_crop_item = None
        self._crop_start = QPointF()
        self._crop_rect_item = None
        
        self._scene.selectionChanged.connect(self._on_selection_changed)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def _on_selection_changed(self):
        self.selection_changed.emit()

    def get_selected_text_item(self):
        for item in self._scene.selectedItems():
            if isinstance(item, PDFTextBlockItem):
                return item
        return None

    def get_selected_line_item(self):
        for item in self._scene.selectedItems():
            if isinstance(item, PDFLineItem):
                return item
        return None

    def get_selected_shape_item(self):
        for item in self._scene.selectedItems():
            if isinstance(item, PDFShapeItem):
                return item
        return None

    def get_selected_image_item(self):
        for item in self._scene.selectedItems():
            if isinstance(item, PDFImageItem):
                return item
        return None

    def load_pages(self, pages_data: list, reset_zoom: bool = True):
        self._scene.clear()
        self._page_rects = []
        y_offset = 0

        for page_idx, page_data in enumerate(pages_data):
            page_rect = QRectF(0, y_offset, page_data.width, page_data.height)
            self._page_rects.append(page_rect)

            bg = self._scene.addRect(
                page_rect,
                QPen(QColor("#3a3a5a"), 1),
                QBrush(QColor("#ffffff")),
            )
            bg.setZValue(-1)

            for img in page_data.images:
                if img.image_data:
                    item = PDFImageItem(
                        img.x, y_offset + img.y,
                        img.width, img.height,
                        img.image_data,
                    )
                    self._scene.addItem(item)

            for tb in page_data.text_blocks:
                item = PDFTextBlockItem(
                    tb.text, tb.x, y_offset + tb.y,
                    tb.font_size, tb.font_name, tb.color,
                    tb.block_id,
                )
                self._scene.addItem(item)

            for le in page_data.lines:
                item = PDFLineItem(
                    le.x1, y_offset + le.y1,
                    le.x2, y_offset + le.y2,
                    le.color, le.width,
                )
                self._scene.addItem(item)

            shapes_list = getattr(page_data, "shapes", [])
            for sh in shapes_list:
                item = PDFShapeItem(
                    sh.type, sh.x, y_offset + sh.y,
                    sh.width, sh.height,
                    sh.color, sh.fill_color, sh.line_width,
                )
                self._scene.addItem(item)

            y_offset += page_data.height + self._page_gap

        if reset_zoom:
            self._zoom = 1.0
            self.resetTransform()
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15
            self._zoom *= factor
            self._zoom = max(0.1, min(self._zoom, 10.0))
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        item = self._scene.itemAt(scene_pos, self.transform())
        if item and not isinstance(item, type(self._scene.items()[-1] if self._scene.items() else None)):
            super().contextMenuEvent(event)
            return

        menu = QMenu(self)
        add_text = menu.addAction("Metin Ekle")
        add_line = menu.addAction("Çizgi Ekle")
        action = menu.exec(event.globalPos())

        if action == add_text:
            text, ok = QInputDialog.getText(self, "Metin Ekle", "Metin:")
            if ok and text:
                item = PDFTextBlockItem(
                    text, scene_pos.x(), scene_pos.y(),
                    12, "normal", (0, 0, 0), -1,
                )
                self._scene.addItem(item)
        elif action == add_line:
            item = PDFLineItem(
                scene_pos.x(), scene_pos.y(),
                scene_pos.x() + 200, scene_pos.y(),
                (0, 0, 0), 1.0,
            )
            self._scene.addItem(item)
            
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Z:
            self.undo()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Y:
            self.redo()
            return
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.save_state()
            self.delete_selected()
        super().keyPressEvent(event)

    def save_state(self):
        state = self.get_all_elements(None)
        self._undo_stack.append(state)
        self._redo_stack.clear()
        if len(self._undo_stack) > 30:
            self._undo_stack.pop(0)

    def undo(self):
        if self._undo_stack:
            current_state = self.get_all_elements(None)
            self._redo_stack.append(current_state)
            state = self._undo_stack.pop()
            self.load_pages(state, reset_zoom=False)

    def redo(self):
        if self._redo_stack:
            current_state = self.get_all_elements(None)
            self._undo_stack.append(current_state)
            state = self._redo_stack.pop()
            self.load_pages(state, reset_zoom=False)

    def _on_scroll(self):
        viewport_rect = self.viewport().rect()
        visible_center = self.mapToScene(viewport_rect.center())
        for idx, rect in enumerate(self._page_rects):
            if rect.contains(visible_center):
                if self._current_page != idx:
                    self._current_page = idx
                    self.page_changed.emit(idx)
                break

    def go_to_page(self, page_idx):
        if 0 <= page_idx < len(self._page_rects):
            rect = self._page_rects[page_idx]
            self.ensureVisible(rect.x() + rect.width()/2, rect.y(), 10, 10)
            self._current_page = page_idx
            self.page_changed.emit(page_idx)

    def mousePressEvent(self, event):
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._crop_start = self.mapToScene(event.pos())
            from PyQt6.QtWidgets import QGraphicsRectItem
            self._crop_rect_item = QGraphicsRectItem(QRectF(self._crop_start, self._crop_start))
            self._crop_rect_item.setPen(QPen(QColor("#f472b6"), 2, Qt.PenStyle.DashLine))
            self._crop_rect_item.setBrush(QBrush(QColor(244, 114, 182, 50)))
            self._crop_rect_item.setZValue(1000)
            self._scene.addItem(self._crop_rect_item)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.save_state()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._crop_mode and self._crop_rect_item:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self._crop_start, current_pos).normalized()
            self._crop_rect_item.setRect(rect)
            return

        super().mouseMoveEvent(event)
        self._guide_lines = []
        selected_items = self._scene.selectedItems()
        if not selected_items:
            self.viewport().update()
            return
            
        item = selected_items[0]
        rect = item.sceneBoundingRect()
        left = rect.left()
        top = rect.top()
        bottom = rect.bottom()
        
        for other in self._scene.items():
            if other == item:
                continue
            if not isinstance(other, (PDFTextBlockItem, PDFLineItem, PDFImageItem)):
                continue
                
            or_ = other.sceneBoundingRect()
            
            # Left edges aligned
            if abs(left - or_.left()) < SNAP_THRESHOLD:
                min_y = min(top, or_.top()) - 20
                max_y = max(bottom, or_.bottom()) + 20
                self._guide_lines.append(
                    (QPointF(or_.left(), min_y), QPointF(or_.left(), max_y))
                )
                
        self.viewport().update()

    def mouseReleaseEvent(self, event):
        if self._crop_mode and event.button() == Qt.MouseButton.LeftButton:
            self._crop_mode = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            
            if self._crop_rect_item:
                crop_scene_rect = self._crop_rect_item.rect()
                self._scene.removeItem(self._crop_rect_item)
                self._crop_rect_item = None
                
                if crop_scene_rect.width() > 10 and crop_scene_rect.height() > 10:
                    self.save_state()
                    item_rect = self._target_crop_item.mapRectFromScene(crop_scene_rect)
                    self._target_crop_item.crop_to_rect(item_rect)
                
                self._target_crop_item = None
            return

        super().mouseReleaseEvent(event)
        self._guide_lines = []
        self.viewport().update()

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self._guide_lines:
            pen = QPen(QColor("#f472b6"), 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            for line in self._guide_lines:
                painter.drawLine(line[0], line[1])

    def get_all_elements(self, pages_data_original):
        result = []
        for page_idx, page_rect in enumerate(self._page_rects):
            y_start = page_rect.y()
            y_end = y_start + page_rect.height()

            page_data = PageData(
                width=page_rect.width(),
                height=page_rect.height(),
            )

            for item in self._scene.items():
                if not hasattr(item, 'sceneBoundingRect'):
                    continue
                item_center_y = item.sceneBoundingRect().center().y()
                if item_center_y < y_start or item_center_y >= y_end:
                    continue

                if isinstance(item, PDFTextBlockItem):
                    data = item.get_data()
                    tb = TextBlock(
                        text=data["text"],
                        x=data["x"],
                        y=data["y"] - y_start,
                        width=data["width"],
                        height=data["height"],
                        font_size=data["font_size"],
                        font_name=data["font_name"],
                        color=data["color"],
                        page_num=page_idx,
                        block_id=data["block_id"],
                        bg_color=data.get("bg_color"),
                        align=data.get("align", 0),
                    )
                    page_data.text_blocks.append(tb)
                elif isinstance(item, PDFLineItem):
                    data = item.get_data()
                    le = LineElement(
                        x1=data["x1"],
                        y1=data["y1"] - y_start,
                        x2=data["x2"],
                        y2=data["y2"] - y_start,
                        color=data["color"],
                        width=data["width"],
                        page_num=page_idx,
                    )
                    page_data.lines.append(le)
                elif isinstance(item, PDFImageItem):
                    data = item.get_data()
                    ie = ImageElement(
                        x=data["x"],
                        y=data["y"] - y_start,
                        width=data["width"],
                        height=data["height"],
                        image_data=data["image_data"],
                        page_num=page_idx,
                    )
                    page_data.images.append(ie)
                elif isinstance(item, PDFShapeItem):
                    data = item.get_data()
                    sh = ShapeElement(
                        type=data["type"],
                        x=data["x"],
                        y=data["y"] - y_start,
                        width=data["width"],
                        height=data["height"],
                        color=data["color"],
                        fill_color=data["fill_color"],
                        line_width=data["line_width"],
                        page_num=page_idx,
                    )
                    page_data.shapes.append(sh)

            result.append(page_data)

        return result

    def zoom_in(self):
        self._zoom *= 1.2
        self.scale(1.2, 1.2)

    def zoom_out(self):
        self._zoom /= 1.2
        self.scale(1/1.2, 1/1.2)

    def zoom_reset(self):
        self.resetTransform()
        self._zoom = 1.0
        if self._scene.sceneRect():
            self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def add_new_text(self):
        self.save_state()
        view_center = self.mapToScene(self.viewport().rect().center())
        item = PDFTextBlockItem(
            "Yeni Metin", view_center.x(), view_center.y(),
            12, "normal", (0, 0, 0), -1,
        )
        self._scene.addItem(item)
        self._scene.clearSelection()
        item.setSelected(True)

    def add_new_line(self):
        self.save_state()
        view_center = self.mapToScene(self.viewport().rect().center())
        item = PDFLineItem(
            view_center.x() - 100, view_center.y(),
            view_center.x() + 100, view_center.y(),
            (0, 0, 0), 1.0,
        )
        self._scene.addItem(item)
        self._scene.clearSelection()
        item.setSelected(True)

    def add_new_shape(self, shape_type: str):
        self.save_state()
        view_center = self.mapToScene(self.viewport().rect().center())
        item = PDFShapeItem(
            shape_type,
            view_center.x() - 50, view_center.y() - 50,
            100, 100,
            color=(0, 0, 0),
            fill_color=None,
            line_width=1.0,
        )
        self._scene.addItem(item)
        self._scene.clearSelection()
        item.setSelected(True)

    def add_new_image(self, image_data: bytes):
        self.save_state()
        view_center = self.mapToScene(self.viewport().rect().center())
        img = QImage()
        img.loadFromData(image_data)
        width, height = 200.0, 200.0
        if not img.isNull():
            ratio = img.width() / img.height()
            if ratio > 1:
                height = 200.0 / ratio
            else:
                width = 200.0 * ratio
                
        item = PDFImageItem(
            view_center.x() - width/2, view_center.y() - height/2,
            width, height, image_data,
        )
        self._scene.addItem(item)
        self._scene.clearSelection()
        item.setSelected(True)

    def delete_selected(self):
        for item in self._scene.selectedItems():
            self._scene.removeItem(item)

    def crop_selected_image(self):
        image_item = self.get_selected_image_item()
        if image_item:
            self._target_crop_item = image_item
            self._crop_mode = True
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self._scene.clearSelection()

    def _get_target_text_items(self) -> list:
        items = list(self._scene.selectedItems())
        focus_item = self._scene.focusItem()
        if focus_item and isinstance(focus_item, PDFTextBlockItem) and focus_item not in items:
            items.append(focus_item)
        return [item for item in items if isinstance(item, PDFTextBlockItem)]

    def toggle_bold(self):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setBold(not f.bold())
            item.setFont(f)

    def toggle_italic(self):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setItalic(not f.italic())
            item.setFont(f)

    def toggle_underline(self):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setUnderline(not f.underline())
            item.setFont(f)

    def toggle_strikeout(self):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setStrikeOut(not f.strikeOut())
            item.setFont(f)

    def change_font(self, font_name: str):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setFamily(font_name)
            item.setFont(f)

    def change_font_size(self, size: int):
        self.save_state()
        for item in self._get_target_text_items():
            f = item.font()
            f.setPixelSize(max(1, size))
            item.setFont(f)

    def change_text_color(self, color: QColor):
        self.save_state()
        for item in self._get_target_text_items():
            item.setDefaultTextColor(color)

    def change_border_color(self, color: QColor):
        self.save_state()
        modified = False
        for item in self._scene.selectedItems():
            if isinstance(item, PDFTextBlockItem):
                item.setDefaultTextColor(color)
                modified = True
            elif isinstance(item, PDFShapeItem):
                item.set_border_color(color)
                modified = True
            elif isinstance(item, PDFLineItem):
                p = item.pen()
                p.setColor(color)
                item.setPen(p)
                modified = True
        if not modified and self._undo_stack:
            self._undo_stack.pop()

    def get_page_rect_for_item(self, item):
        item_rect = item.sceneBoundingRect()
        item_y_center = item_rect.center().y()
        for page_rect in self._page_rects:
            if page_rect.top() <= item_y_center <= page_rect.bottom():
                return page_rect
        if self._page_rects:
            closest_rect = self._page_rects[0]
            min_dist = abs(closest_rect.center().y() - item_y_center)
            for page_rect in self._page_rects[1:]:
                dist = abs(page_rect.center().y() - item_y_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_rect = page_rect
            return closest_rect
        return QRectF(0, 0, 595, 842)

    def get_visual_rect(self, item):
        rect = item.sceneBoundingRect()
        if isinstance(item, PDFTextBlockItem):
            doc = item.document()
            ideal_w = doc.idealWidth()
            text_w = item.textWidth()
            if text_w > 0 and ideal_w < text_w:
                align_flag = doc.defaultTextOption().alignment()
                if align_flag & Qt.AlignmentFlag.AlignRight:
                    offset = text_w - ideal_w
                    return QRectF(rect.left() + offset, rect.top(), ideal_w, rect.height())
                elif align_flag & Qt.AlignmentFlag.AlignHCenter:
                    offset = (text_w - ideal_w) / 2
                    return QRectF(rect.left() + offset, rect.top(), ideal_w, rect.height())
        return rect

    def change_alignment(self, alignment_text: str):
        self.save_state()
        modified = False
        
        selected_items = [item for item in self._scene.selectedItems() 
                          if isinstance(item, (PDFTextBlockItem, PDFLineItem, PDFImageItem, PDFShapeItem))]
        
        # Default margin for page-relative alignment: 1.9 cm
        # 1 cm = 28.35 pt
        margin = 1.9 * 28.35
        
        if len(selected_items) > 1:
            # Selection-relative alignment
            if alignment_text == "Sola Hizala":
                ref_left = min(self.get_visual_rect(item).left() for item in selected_items)
                for item in selected_items:
                    if isinstance(item, PDFTextBlockItem):
                        item.setTextWidth(-1)
                        item.set_alignment(Qt.AlignmentFlag.AlignLeft)
                        item.setPos(ref_left, item.pos().y())
                        modified = True
                    else:
                        item_rect = item.sceneBoundingRect()
                        dx = ref_left - item_rect.left()
                        if dx != 0:
                            item.setPos(item.pos().x() + dx, item.pos().y())
                            modified = True
                            
            elif alignment_text == "Ortala":
                min_left = min(self.get_visual_rect(item).left() for item in selected_items)
                max_right = max(self.get_visual_rect(item).right() for item in selected_items)
                ref_center = (min_left + max_right) / 2.0
                for item in selected_items:
                    if isinstance(item, PDFTextBlockItem):
                        item.setTextWidth(-1)
                        item.set_alignment(Qt.AlignmentFlag.AlignHCenter)
                        ideal_w = item.document().idealWidth()
                        item.setPos(ref_center - ideal_w / 2.0, item.pos().y())
                        modified = True
                    else:
                        item_rect = item.sceneBoundingRect()
                        dx = ref_center - item_rect.center().x()
                        if dx != 0:
                            item.setPos(item.pos().x() + dx, item.pos().y())
                            modified = True
                            
            elif alignment_text == "Sağa Hizala":
                ref_right = max(self.get_visual_rect(item).right() for item in selected_items)
                for item in selected_items:
                    if isinstance(item, PDFTextBlockItem):
                        item.setTextWidth(-1)
                        item.set_alignment(Qt.AlignmentFlag.AlignRight)
                        ideal_w = item.document().idealWidth()
                        item.setPos(ref_right - ideal_w, item.pos().y())
                        modified = True
                    else:
                        item_rect = item.sceneBoundingRect()
                        dx = ref_right - item_rect.right()
                        if dx != 0:
                            item.setPos(item.pos().x() + dx, item.pos().y())
                            modified = True
        else:
            # Page-relative alignment
            for item in selected_items:
                page_rect = self.get_page_rect_for_item(item)
                
                if isinstance(item, PDFTextBlockItem):
                    item.setTextWidth(page_rect.width() - 2 * margin)
                    item.setPos(page_rect.left() + margin, item.pos().y())
                    
                    align_map = {
                        "Sola Hizala": Qt.AlignmentFlag.AlignLeft,
                        "Ortala": Qt.AlignmentFlag.AlignHCenter,
                        "Sağa Hizala": Qt.AlignmentFlag.AlignRight,
                    }
                    align_flag = align_map.get(alignment_text, Qt.AlignmentFlag.AlignLeft)
                    item.set_alignment(align_flag)
                    modified = True
                    
                elif isinstance(item, (PDFLineItem, PDFImageItem, PDFShapeItem)):
                    item_rect = item.sceneBoundingRect()
                    item_w = item_rect.width()
                    
                    effective_margin = margin
                    if item_w > page_rect.width() - 2 * margin:
                        effective_margin = max(0.0, (page_rect.width() - item_w) / 2)
                        
                    if alignment_text == "Sola Hizala":
                        target_left = page_rect.left() + effective_margin
                    elif alignment_text == "Ortala":
                        target_left = page_rect.left() + (page_rect.width() - item_w) / 2
                    elif alignment_text == "Sağa Hizala":
                        target_left = page_rect.right() - effective_margin - item_w
                    else:
                        target_left = item_rect.left()
                        
                    dx = target_left - item_rect.left()
                    if dx != 0:
                        item.setPos(item.pos().x() + dx, item.pos().y())
                        modified = True
                        
        if not modified and self._undo_stack:
            self._undo_stack.pop()

    def change_line_width(self, width: float):
        self.save_state()
        for item in self._scene.selectedItems():
            if isinstance(item, PDFLineItem):
                p = item.pen()
                p.setWidthF(width)
                item.setPen(p)
            elif isinstance(item, PDFShapeItem):
                item.set_line_width(width)

    def change_line_length(self, length: float):
        self.save_state()
        for item in self._scene.selectedItems():
            if isinstance(item, PDFLineItem):
                line = item.line()
                item.setLine(line.x1(), line.y1(), line.x1() + length, line.y2())

    def add_new_page(self):
        if not self._page_rects:
            return
        
        last_rect = self._page_rects[-1]
        y_offset = last_rect.y() + last_rect.height() + self._page_gap
        
        new_rect = QRectF(0, y_offset, last_rect.width(), last_rect.height())
        self._page_rects.append(new_rect)
        
        bg = self._scene.addRect(
            new_rect,
            QPen(QColor("#3a3a5a"), 1),
            QBrush(QColor("#ffffff")),
        )
        bg.setZValue(-1)
        self._scene.setSceneRect(self._scene.itemsBoundingRect())

    def delete_last_page(self):
        if len(self._page_rects) <= 1:
            return
            
        last_rect = self._page_rects.pop()
        
        y_start = last_rect.y()
        y_end = last_rect.y() + last_rect.height()
        
        for item in self._scene.items():
            item_y = item.pos().y() if hasattr(item, 'pos') else -1
            if item_y == -1 and hasattr(item, 'rect'):
                item_y = item.rect().y()
                
            if y_start <= item_y <= y_end:
                self._scene.removeItem(item)
                
        self._scene.setSceneRect(self._scene.itemsBoundingRect())
