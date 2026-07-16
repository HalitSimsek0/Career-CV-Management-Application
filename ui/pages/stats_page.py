from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QApplication, QPushButton, QComboBox,
)
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtCore import Qt
from services.stats_service import StatsService
from services.application_service import ApplicationService
from ui.widgets.status_badge import StatusBadge
import config


class StatsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_service = StatsService()
        self._app_service = ApplicationService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("İstatistikler & Analiz")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(16)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._total_card = self._create_metric_card("Toplam Başvuru", "0")
        self._companies_card = self._create_metric_card("Farklı Şirket", "0")
        self._response_card = self._create_metric_card("Cevap Oranı", "0%")
        self._success_card = self._create_metric_card("Başarı Oranı", "0%")
        self._rejection_card = self._create_metric_card("Red Oranı", "0%")
        self._interview_card = self._create_metric_card("Mülakat Oranı", "0%")
        cards_row.addWidget(self._total_card)
        cards_row.addWidget(self._companies_card)
        cards_row.addWidget(self._response_card)
        cards_row.addWidget(self._success_card)
        cards_row.addWidget(self._rejection_card)
        cards_row.addWidget(self._interview_card)
        self._content_layout.addLayout(cards_row)

        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_frame.setMaximumHeight(200)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setSpacing(2)
        status_layout.setContentsMargins(12, 8, 12, 8)
        s_title = QLabel("Durum Dağılımı")
        s_title.setStyleSheet("font-weight: 800; color: #60a5fa; font-size: 14px; background: transparent;")
        status_layout.addWidget(s_title)
        self._status_list_layout = QVBoxLayout()
        self._status_list_layout.setSpacing(1)
        status_layout.addLayout(self._status_list_layout)
        status_layout.addStretch()
        charts_row.addWidget(status_frame)

        monthly_frame = QFrame()
        monthly_frame.setObjectName("card")
        monthly_frame.setMaximumHeight(200)
        monthly_layout = QVBoxLayout(monthly_frame)
        monthly_layout.setSpacing(2)
        monthly_layout.setContentsMargins(12, 8, 12, 8)
        m_title = QLabel("Aylık Başvurular")
        m_title.setStyleSheet("font-weight: 800; color: #60a5fa; font-size: 14px; background: transparent;")
        monthly_layout.addWidget(m_title)
        self._monthly_list_layout = QVBoxLayout()
        self._monthly_list_layout.setSpacing(1)
        monthly_layout.addLayout(self._monthly_list_layout)
        monthly_layout.addStretch()
        charts_row.addWidget(monthly_frame)

        self._content_layout.addLayout(charts_row)

        top_frame = QFrame()
        top_frame.setObjectName("card")
        top_layout = QVBoxLayout(top_frame)
        
        top_header_layout = QHBoxLayout()
        top_title = QLabel("En Çok Başvurulan Şirketler (tıklayın)")
        top_title.setStyleSheet("font-weight: 800; color: #60a5fa; font-size: 15px; background: transparent;")
        top_header_layout.addWidget(top_title)
        top_header_layout.addStretch()
        
        self._top_limit_combo = QComboBox()
        self._top_limit_combo.addItems(["İlk 10", "İlk 20", "Hepsi"])
        self._top_limit_combo.currentIndexChanged.connect(self._refresh_data)
        self._top_limit_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 150);
                border: 1px solid rgba(255, 255, 255, 200);
                border-radius: 6px;
                padding: 4px 8px;
                color: #4b5563;
                font-weight: bold;
            }
        """)
        top_header_layout.addWidget(self._top_limit_combo)
        
        top_layout.addLayout(top_header_layout)
        
        self._top_companies_layout = QVBoxLayout()
        top_layout.addLayout(self._top_companies_layout)
        self._content_layout.addWidget(top_frame)

        db_info_label = QLabel(f"Veritabanı Konumu: {config.DB_PATH}")
        db_info_label.setStyleSheet("color: #a78bfa; font-size: 11px;")
        db_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._content_layout.addWidget(db_info_label)

        self._content_layout.addStretch()

    def _create_metric_card(self, label, value):
        card = QFrame()
        card.setObjectName("statCard")
        card.setMinimumWidth(130)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)
        val = QLabel(value)
        val.setObjectName("statValue")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(val)
        lbl = QLabel(label)
        lbl.setObjectName("statLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl)
        card._val = val
        return card

    def _refresh_data(self):
        overview = self._stats_service.get_overview()
        self._total_card._val.setText(str(overview["total"]))
        self._companies_card._val.setText(str(overview["unique_companies"]))
        self._response_card._val.setText(f"{self._stats_service.get_response_rate():.0f}%")
        self._success_card._val.setText(f"{self._stats_service.get_success_rate():.0f}%")
        self._rejection_card._val.setText(f"{self._stats_service.get_rejection_rate():.0f}%")
        self._interview_card._val.setText(f"{self._stats_service.get_interview_rate():.0f}%")

        while self._status_list_layout.count():
            item = self._status_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if overview["by_status"]:
            status_map = {
                "applied": "Başvuruldu", "interview": "Mülakat",
                "technical_test": "Teknik Test", "offer": "Teklif",
                "rejected": "Reddedildi", "no_response": "Cevap Yok",
                "withdrawn": "Geri Çekildi", "accepted": "Kabul Edildi"
            }
            for k, v in overview["by_status"].items():
                lbl = QLabel(f"• {status_map.get(k, k)}: <b>{v}</b>")
                lbl.setTextFormat(Qt.TextFormat.RichText)
                lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lbl.setStyleSheet("font-size: 14px; color: #a78bfa; padding: 1px 0px; background: transparent;")
                self._status_list_layout.addWidget(lbl)

        while self._monthly_list_layout.count():
            item = self._monthly_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if overview["monthly"]:
            for m, c in overview["monthly"]:
                lbl = QLabel(f"• {m}: <b>{c}</b> başvuru")
                lbl.setTextFormat(Qt.TextFormat.RichText)
                lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lbl.setStyleSheet("font-size: 14px; color: #a78bfa; padding: 1px 0px; background: transparent;")
                self._monthly_list_layout.addWidget(lbl)

        while self._top_companies_layout.count():
            item = self._top_companies_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        top_companies = overview.get("top_companies", [])
        limit_idx = self._top_limit_combo.currentIndex()
        if limit_idx == 0:
            top_companies = top_companies[:10]
        elif limit_idx == 1:
            top_companies = top_companies[:20]

        for i, (name, count) in enumerate(top_companies):
            accordion = CompanyAccordionWidget(name, count, i + 1)
            self._top_companies_layout.addWidget(accordion)


class CompanyAccordionWidget(QWidget):
    def __init__(self, name, count, rank, parent=None):
        super().__init__(parent)
        self._name = name
        self._count = count
        self._rank = rank
        self._is_expanded = False
        self.setMaximumWidth(750)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._header = QWidget()
        self._header.setFixedHeight(48)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 100);
                border: 1px solid rgba(255, 255, 255, 150);
                border-radius: 12px;
                padding: 2px;
            }
            QWidget:hover {
                background-color: rgba(255, 255, 255, 200);
                border-color: rgba(96, 165, 250, 100);
            }
        """)
        h_layout = QHBoxLayout(self._header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        
        rank_label = QLabel(f"#{rank}")
        rank_label.setStyleSheet("color: #60a5fa; font-weight: bold; min-width: 30px; background: transparent; border: none;")
        h_layout.addWidget(rank_label)
 
        name_label = QLabel(name)
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        name_label.setCursor(Qt.CursorShape.IBeamCursor)
        name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #8b5cf6; background: transparent; border: none;")
        h_layout.addWidget(name_label)
        h_layout.addStretch()
 
        cnt_label = QLabel(f"{count} başvuru")
        cnt_label.setStyleSheet("color: #c4b5fd; font-size: 12px; background: transparent; border: none;")
        h_layout.addWidget(cnt_label)
 
        self._arrow = QLabel("▼")
        self._arrow.setStyleSheet("color: #a78bfa; font-size: 12px; background: transparent; border: none;")
        h_layout.addWidget(self._arrow)
        
        layout.addWidget(self._header)
        
        self._detail_widget = QWidget()
        self._detail_widget.hide()
        self._detail_layout = QVBoxLayout(self._detail_widget)
        self._detail_layout.setContentsMargins(16, 8, 16, 16)
        self._detail_layout.setSpacing(8)
        
        layout.addWidget(self._detail_widget)
        self._header.mousePressEvent = self._toggle
        
    def _toggle(self, event):
        self._is_expanded = not self._is_expanded
        if self._is_expanded:
            self._arrow.setText("▲")
            self._load_data()
            self._detail_widget.show()
        else:
            self._arrow.setText("▼")
            self._detail_widget.hide()
            
    def _create_mini_card(self, app):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(48)
        card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(255, 255, 255, 180);
                border: 1px solid rgba(255, 255, 255, 220);
                border-radius: 10px;
                padding: 8px 12px;
            }
            QFrame#card:hover {
                border-color: rgba(96, 165, 250, 150);
                background-color: rgba(255, 255, 255, 210);
            }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 6, 12, 6)
        card_layout.setSpacing(12)

        pos_label = QLabel(app.position)
        pos_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #8b5cf6; background: transparent;")
        card_layout.addWidget(pos_label)
        
        card_layout.addStretch()

        badge = StatusBadge(app.status)
        card_layout.addWidget(badge)

        date_label = QLabel(app.application_date)
        date_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #a78bfa; background: transparent;")
        card_layout.addWidget(date_label)

        return card

    def _load_data(self):
        # Clear existing items
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        from repositories.application_repository import ApplicationRepository
        repo = ApplicationRepository()
        apps = repo.get_by_company(self._name)
        
        for app in apps:
            card = self._create_mini_card(app)
            self._detail_layout.addWidget(card)
