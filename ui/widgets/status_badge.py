from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from ui.style_manager import StyleManager


class StatusBadge(QLabel):
    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self._status = status
        self._update_display()

    def _update_display(self):
        display_map = {
            "applied": "Başvuruldu",
            "interview": "Mülakat",
            "technical_test": "Teknik Test",
            "offer": "Teklif",
            "rejected": "Reddedildi",
            "no_response": "Cevap Yok",
            "withdrawn": "Geri Çekildi",
            "accepted": "Kabul Edildi",
        }
        self.setText(display_map.get(self._status, self._status))
        color = StyleManager.get_status_color(self._status)
        self.setFixedHeight(24)
        self.setMinimumWidth(90)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color}18;
                color: {color};
                border: 1px solid {color}40;
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_status(self, status: str):
        self._status = status
        self._update_display()
