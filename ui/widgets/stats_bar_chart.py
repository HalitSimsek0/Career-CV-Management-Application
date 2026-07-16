from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient


class StatsBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._title = ""
        self.setMinimumHeight(250)

    def set_data(self, data: dict, title: str = ""):
        self._data = data
        self._title = title
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        margin_left = 50
        margin_right = 20
        margin_top = 40
        margin_bottom = 80

        if self._title:
            painter.setPen(QColor("#1e40af"))
            painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            painter.drawText(QRectF(0, 5, w, 30), Qt.AlignmentFlag.AlignCenter, self._title)

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom
        if chart_w <= 0 or chart_h <= 0:
            painter.end()
            return

        max_val = max(self._data.values()) if self._data.values() else 1
        bar_count = len(self._data)
        if bar_count == 0:
            painter.end()
            return

        bar_width = min(chart_w / bar_count * 0.6, 50)
        gap = (chart_w - bar_width * bar_count) / (bar_count + 1)

        painter.setPen(QPen(QColor("#eff6ff"), 1))
        for i in range(5):
            y = margin_top + chart_h * i / 4
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            val = max_val * (4 - i) / 4
            painter.setPen(QColor("#c4b5fd"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                QRectF(0, y - 10, margin_left - 5, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(int(val)),
            )
            painter.setPen(QPen(QColor("#eff6ff"), 1))

        from utils.skill_dictionary import STATUS_COLORS
        fallback_colors = ["#60a5fa", "#60a5fa", "#f472b6", "#10b981", "#f59e0b",
                          "#60a5fa", "#60a5fa", "#14b8a6"]

        for idx, (label, value) in enumerate(self._data.items()):
            x = margin_left + gap + idx * (bar_width + gap)
            bar_h = (value / max_val) * chart_h if max_val > 0 else 0
            y = margin_top + chart_h - bar_h

            color = STATUS_COLORS.get(label, fallback_colors[idx % len(fallback_colors)])
            grad = QLinearGradient(x, y, x, margin_top + chart_h)
            grad.setColorAt(0, QColor(color))
            grad.setColorAt(1, QColor(color).lighter(130))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)

            rect = QRectF(x, y, bar_width, bar_h)
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QColor("#8b5cf6"))
            painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            painter.drawText(
                QRectF(x, y - 22, bar_width, 20),
                Qt.AlignmentFlag.AlignCenter,
                str(value),
            )

            painter.setPen(QColor("#a78bfa"))
            painter.setFont(QFont("Segoe UI", 9))
            display_map = {
                "applied": "Başvuru",
                "interview": "Mülakat",
                "technical_test": "Test",
                "offer": "Teklif",
                "rejected": "Red",
                "no_response": "Cevapsız",
                "withdrawn": "Çekildi",
                "accepted": "Kabul",
            }
            display = display_map.get(label, label[:8])
            painter.save()
            painter.translate(x + bar_width / 2, margin_top + chart_h + 10)
            painter.rotate(35)
            painter.drawText(0, 0, display)
            painter.restore()

        painter.end()
