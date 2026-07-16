import logging
import fitz
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    text: str
    x: float
    y: float
    width: float
    height: float
    font_size: float
    font_name: str
    color: tuple = (0, 0, 0)
    page_num: int = 0
    block_id: int = 0
    original_rect: Optional[tuple] = None
    bg_color: Optional[tuple] = None
    align: int = 0

@dataclass
class LineElement:
    x1: float
    y1: float
    x2: float
    y2: float
    color: tuple = (0, 0, 0)
    width: float = 1.0
    page_num: int = 0

@dataclass
class ImageElement:
    x: float
    y: float
    width: float
    height: float
    image_data: bytes = b""
    page_num: int = 0
    xref: int = 0

@dataclass
class ShapeElement:
    type: str  # "rect" or "ellipse"
    x: float
    y: float
    width: float
    height: float
    color: tuple = (0, 0, 0)
    fill_color: Optional[tuple] = None
    line_width: float = 1.0
    page_num: int = 0

@dataclass
class PageData:
    width: float
    height: float
    text_blocks: List[TextBlock] = field(default_factory=list)
    lines: List[LineElement] = field(default_factory=list)
    images: List[ImageElement] = field(default_factory=list)
    shapes: List[ShapeElement] = field(default_factory=list)


class PDFEditService:
    def __init__(self):
        self._doc = None
        self._file_path = ""
        self._pages_data: List[PageData] = []

    # Context manager support to prevent resource leaks
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def open_pdf(self, file_path: str) -> List[PageData]:
        self._file_path = file_path
        self._doc = fitz.open(file_path)
        self._pages_data = []

        for page_num, page in enumerate(self._doc):
            page_data = PageData(
                width=page.rect.width,
                height=page.rect.height,
            )

            block_id = 0
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if not span["text"].strip():
                                continue
                            color_int = span.get("color", 0)
                            r = (color_int >> 16) & 0xFF
                            g = (color_int >> 8) & 0xFF
                            b = color_int & 0xFF
                            tb = TextBlock(
                                text=span["text"],
                                x=span["bbox"][0],
                                y=span["bbox"][1],
                                width=span["bbox"][2] - span["bbox"][0],
                                height=span["bbox"][3] - span["bbox"][1],
                                font_size=span["size"],
                                font_name=span["font"],
                                color=(r / 255.0, g / 255.0, b / 255.0),
                                page_num=page_num,
                                block_id=block_id,
                                original_rect=tuple(span["bbox"]),
                            )
                            page_data.text_blocks.append(tb)
                            block_id += 1

            drawings = page.get_drawings()
            for d in drawings:
                for item in d.get("items", []):
                    if item[0] == "l":
                        le = LineElement(
                            x1=item[1].x,
                            y1=item[1].y,
                            x2=item[2].x,
                            y2=item[2].y,
                            color=d.get("color", (0, 0, 0)) or (0, 0, 0),
                            width=d.get("width", 1.0),
                            page_num=page_num,
                        )
                        page_data.lines.append(le)

            for img_info in page.get_images(full=True):
                xref = img_info[0]
                try:
                    img_rects = page.get_image_rects(xref)
                    if img_rects:
                        rect = img_rects[0]
                        pix = fitz.Pixmap(self._doc, xref)
                        if pix.n - pix.alpha > 3:
                            pix1 = fitz.Pixmap(fitz.csRGB, pix)
                            pix = pix1
                        if pix.alpha:
                            image_data = pix.tobytes("png")
                        else:
                            # Optimize by saving as JPEG if there is no transparency
                            image_data = pix.tobytes("jpeg")
                        pix = None

                        ie = ImageElement(
                            x=rect.x0,
                            y=rect.y0,
                            width=rect.width,
                            height=rect.height,
                            image_data=image_data,
                            page_num=page_num,
                            xref=xref,
                        )
                        page_data.images.append(ie)
                except Exception:
                    logger.warning(
                        "Sayfa %d, xref %d: Görsel çıkarılamadı",
                        page_num, xref,
                    )

            self._pages_data.append(page_data)

        return self._pages_data

    def _select_font(self, font_name_original: str) -> str:
        """Select best available built-in font based on the original font style."""
        lower = font_name_original.lower()
        if "bold" in lower and "italic" in lower:
            return "hebi"
        elif "bold" in lower:
            return "hebo"
        elif "italic" in lower:
            return "heit"
        return "helv"

    def _insert_text_safe(self, page, tb: TextBlock):
        """Insert text with multiple fallback strategies for robustness."""
        font_name = self._select_font(tb.font_name)
        r, g, b = tb.color
        text_color = (r, g, b)
        align_val = getattr(tb, "align", 0)

        # Draw background if present
        bg_color = getattr(tb, "bg_color", None)
        if bg_color is not None:
            try:
                shape = page.new_shape()
                rect = fitz.Rect(tb.x, tb.y, tb.x + tb.width, tb.y + tb.height)
                shape.draw_rect(rect)
                shape.finish(color=bg_color, fill=bg_color, width=0)
                shape.commit()
            except Exception:
                logger.debug("Arka plan rengi uygulanamadı: block_id=%d", tb.block_id)

        if tb.width > 0 and tb.height > 0:
            # Prevent unwanted wrapping by giving ample width for left/center aligned text
            rect_x0 = tb.x
            rect_x1 = tb.x + tb.width
            if align_val == 0:  # Left
                rect_x1 += 500
            elif align_val == 1:  # Center
                rect_x0 -= 100
                rect_x1 += 100
            elif align_val == 2:  # Right
                rect_x0 -= 500
                
            rect = fitz.Rect(rect_x0, tb.y, rect_x1, tb.y + tb.height + 20)
            # Try with original font/color first
            try:
                page.insert_textbox(
                    rect, tb.text,
                    fontsize=tb.font_size, fontname=font_name,
                    color=text_color, align=align_val,
                )
                return
            except Exception:
                pass
            # Fallback: default font/black
            try:
                page.insert_textbox(
                    rect, tb.text,
                    fontsize=tb.font_size, fontname="helv",
                    color=(0, 0, 0), align=align_val,
                )
                return
            except Exception:
                pass
            # Last resort: insert_text
            insertion_point = fitz.Point(tb.x, tb.y + tb.font_size)
            page.insert_text(
                insertion_point, tb.text,
                fontsize=tb.font_size, fontname="helv", color=(0, 0, 0),
            )
        else:
            insertion_point = fitz.Point(tb.x, tb.y + tb.font_size)
            try:
                page.insert_text(
                    insertion_point, tb.text,
                    fontsize=tb.font_size, fontname=font_name, color=text_color,
                )
            except Exception:
                page.insert_text(
                    insertion_point, tb.text,
                    fontsize=tb.font_size, fontname="helv", color=(0, 0, 0),
                )

    def save_pdf(self, output_path: str, pages_data: List[PageData]):
        new_doc = fitz.open()

        for page_data in pages_data:
            page = new_doc.new_page(
                width=page_data.width,
                height=page_data.height,
            )

            for tb in page_data.text_blocks:
                self._insert_text_safe(page, tb)

            for le in page_data.lines:
                shape = page.new_shape()
                shape.draw_line(
                    fitz.Point(le.x1, le.y1),
                    fitz.Point(le.x2, le.y2),
                )
                shape.finish(
                    color=le.color if isinstance(le.color, tuple) else (0, 0, 0),
                    width=le.width,
                )
                shape.commit()

            for ie in page_data.images:
                if ie.image_data:
                    rect = fitz.Rect(ie.x, ie.y, ie.x + ie.width, ie.y + ie.height)
                    try:
                        page.insert_image(rect, stream=ie.image_data)
                    except Exception:
                        logger.warning("Görsel eklenemedi: xref=%d", ie.xref)

            shapes_list = getattr(page_data, "shapes", [])
            for sh in shapes_list:
                try:
                    shape = page.new_shape()
                    rect = fitz.Rect(sh.x, sh.y, sh.x + sh.width, sh.y + sh.height)
                    if sh.type == "rect":
                        shape.draw_rect(rect)
                    elif sh.type == "ellipse":
                        shape.draw_oval(rect)

                    border_color = sh.color if isinstance(sh.color, tuple) else (0, 0, 0)
                    fill_color = sh.fill_color if isinstance(sh.fill_color, tuple) else None
                    shape.finish(
                        color=border_color,
                        fill=fill_color,
                        width=sh.line_width,
                    )
                    shape.commit()
                except Exception:
                    logger.warning("Şekil eklenemedi: type=%s", sh.type)

        new_doc.save(output_path)
        new_doc.close()

    def close(self):
        if self._doc:
            self._doc.close()
            self._doc = None

    def get_page_count(self) -> int:
        return len(self._pages_data)
