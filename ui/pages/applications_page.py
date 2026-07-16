from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QDialog, QFormLayout, QDateEdit,
    QFrame, QMessageBox, QScrollArea, QApplication, QCompleter, 
    QCalendarWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor
from services.application_service import ApplicationService
from models.job_application import JobApplication
from ui.widgets.status_badge import StatusBadge


class DateFilterDialog(QDialog):
    def __init__(self, active_dates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tarihe Göre Filtrele")
        self.setFixedSize(350, 300)
        self.selected_date = None
        self.active_dates = active_dates
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        
        # Highlight active dates
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#a78bfa"))
        fmt.setForeground(QColor("white"))
        fmt.setFontWeight(700)
        
        for date_str in self.active_dates:
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            if d.isValid():
                self.calendar.setDateTextFormat(d, fmt)
                
        self.calendar.clicked.connect(self._on_date_clicked)
        layout.addWidget(self.calendar)
        
    def _on_date_clicked(self, qdate):
        date_str = qdate.toString("yyyy-MM-dd")
        if date_str in self.active_dates:
            self.selected_date = date_str
            self.accept()
        else:
            # If clicked on a date with no applications, do nothing or show a message
            pass

class DatePickerButton(QPushButton):
    def __init__(self, date_str=None, parent=None):
        super().__init__(parent)
        from PyQt6.QtCore import QDate, Qt
        self._date = QDate.fromString(date_str, "yyyy-MM-dd") if date_str else QDate.currentDate()
        self.setText(self._date.toString("yyyy-MM-dd"))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 10px;
                background: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                height: 38px;
                font-size: 14px;
                color: #8b5cf6;
            }
            QPushButton:hover {
                border-color: #60a5fa;
                background-color: #f8fafc;
            }
        """)
        self.clicked.connect(self._show_calendar)
        
    def date(self):
        return self._date
        
    def setDate(self, date):
        self._date = date
        self.setText(self._date.toString("yyyy-MM-dd"))
        
    def _show_calendar(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget
        from PyQt6.QtCore import Qt
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup)
        dialog.setStyleSheet("QDialog { background: white; border: 1px solid #ccc; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        cal = QCalendarWidget()
        cal.setGridVisible(True)
        cal.setSelectedDate(self._date)
        cal.clicked.connect(self._on_date_selected)
        cal.clicked.connect(dialog.accept)
        
        layout.addWidget(cal)
        
        pos = self.mapToGlobal(self.rect().bottomLeft())
        dialog.move(pos)
        dialog.exec()
        
    def _on_date_selected(self, date):
        self.setDate(date)

class ApplicationDialog(QDialog):
    def __init__(self, app=None, parent=None, company_names=None):
        super().__init__(parent)
        self._app = app
        self._company_names = company_names or []
        self.setWindowTitle("Başvuru Ekle" if not app else "Başvuru Düzenle")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(18)
        layout.setContentsMargins(30, 30, 30, 30)

        self._company = QLineEdit()
        self._company.setPlaceholderText("Şirket adı")
        
        if self._company_names:
            completer = QCompleter(self._company_names, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self._company.setCompleter(completer)
            
        layout.addRow("Şirket:", self._company)

        self._position = QLineEdit()
        self._position.setPlaceholderText("Pozisyon / Alan (ör: Data Science)")
        layout.addRow("Pozisyon:", self._position)

        self._status = QComboBox()
        statuses = [
            ("Başvuruldu", "applied"),
            ("Mülakat", "interview"),
            ("Reddedildi", "rejected"),
            ("Kabul Edildi", "accepted"),
        ]
        for display, value in statuses:
            self._status.addItem(display, value)
        layout.addRow("Durum:", self._status)

        self._date = DatePickerButton()
        layout.addRow("Tarih:", self._date)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Kaydet")
        save_btn.setObjectName("primaryBtn")
        save_btn.setMinimumWidth(120)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addRow(btn_row)

        if self._app:
            self._company.setText(self._app.company_name)
            self._position.setText(self._app.position)
            idx = self._status.findData(self._app.status)
            if idx >= 0:
                self._status.setCurrentIndex(idx)
            if self._app.application_date:
                d = QDate.fromString(self._app.application_date, "yyyy-MM-dd")
                if d.isValid():
                    self._date.setDate(d)

    def get_data(self) -> dict:
        from utils.string_utils import turkish_upper
        pos = self._position.text().strip()
        if not pos:
            pos = "Software"
        return {
            "company_name": turkish_upper(self._company.text().strip()),
            "position": pos,
            "status": self._status.currentData(),
            "application_date": self._date.date().toString("yyyy-MM-dd"),
        }


class ApplicationsPage(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = ApplicationService()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("Başvurularım")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._filter = QComboBox()
        self._filter.addItem("Tümü", "all")
        self._filter.addItem("Başvuruldu", "applied")
        self._filter.addItem("Mülakat", "interview")
        self._filter.addItem("Reddedildi", "rejected")
        self._filter.addItem("Kabul Edildi", "accepted")
        self._filter.currentIndexChanged.connect(self._on_filter)
        header.addWidget(self._filter)

        self._sort_combo = QComboBox()
        self._sort_combo.addItem("Tarihe Göre (Yeni-Eski)", "date_desc")
        self._sort_combo.addItem("Tarihe Göre (Eski-Yeni)", "date_asc")
        self._sort_combo.addItem("Ekleme Zamanına Göre (Yeni-Eski)", "created_desc")
        self._sort_combo.addItem("Ekleme Zamanına Göre (Eski-Yeni)", "created_asc")
        self._sort_combo.addItem("Alfabeye Göre (A-Z)", "alpha_asc")
        self._sort_combo.addItem("Alfabeye Göre (Z-A)", "alpha_desc")
        self._sort_combo.currentIndexChanged.connect(self._on_filter)
        header.addWidget(self._sort_combo)

        date_filter_btn = QPushButton("Tarih Seç")
        date_filter_btn.clicked.connect(self._open_date_filter)
        header.addWidget(date_filter_btn)
        
        self._clear_filter_btn = QPushButton("Sıfırla")
        self._clear_filter_btn.clicked.connect(self._clear_filters)
        self._clear_filter_btn.hide()
        header.addWidget(self._clear_filter_btn)

        add_btn = QPushButton("+ Yeni Başvuru")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumWidth(140)
        add_btn.clicked.connect(self._add_application)
        header.addWidget(add_btn)

        layout.addLayout(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self._total_label = self._create_stat_card("Toplam Başvuru", "0")
        self._companies_label = self._create_stat_card("Farklı Şirket", "0")
        
        self._total_label.setFixedHeight(165)
        self._companies_label.setFixedHeight(165)
        
        self._total_label.setSizePolicy(self._total_label.sizePolicy().Policy.Expanding, self._total_label.sizePolicy().Policy.Fixed)
        self._companies_label.setSizePolicy(self._companies_label.sizePolicy().Policy.Expanding, self._companies_label.sizePolicy().Policy.Fixed)
        
        self._daily_stats_card = QFrame()
        self._daily_stats_card.setObjectName("statCard")
        self._daily_stats_card.setFixedHeight(165)
        self._daily_stats_card.setSizePolicy(self._daily_stats_card.sizePolicy().Policy.Expanding, self._daily_stats_card.sizePolicy().Policy.Fixed)
        daily_card_layout = QVBoxLayout(self._daily_stats_card)
        daily_card_layout.setContentsMargins(8, 8, 8, 8)
        daily_card_layout.setSpacing(2)
        
        daily_scroll = QScrollArea()
        daily_scroll.setWidgetResizable(True)
        daily_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self._daily_container = QWidget()
        self._daily_layout = QGridLayout(self._daily_container)
        self._daily_layout.setSpacing(8)
        self._daily_layout.setContentsMargins(0, 0, 0, 0)
        self._daily_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        daily_scroll.setWidget(self._daily_container)
        daily_card_layout.addWidget(daily_scroll)
        
        stats_row.addWidget(self._total_label, 1)
        stats_row.addWidget(self._companies_label, 1)
        stats_row.addWidget(self._daily_stats_card, 4)
        layout.addLayout(stats_row)

        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Şirket veya pozisyon ara...")
        self._search.setMinimumHeight(42)
        self._search.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 10px 16px;
                border: 1px solid rgba(255, 255, 255, 200);
                border-radius: 10px;
                background: rgba(255, 255, 255, 150);
                color: #8b5cf6;
            }
            QLineEdit:focus {
                border: 2px solid rgba(96, 165, 250, 150);
                background: rgba(255, 255, 255, 200);
            }
        """)
        self._search.textChanged.connect(self._on_search)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(12)
        self._list_layout.setContentsMargins(0, 4, 0, 4)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll)
        layout.setStretchFactor(scroll, 1)

    def _create_stat_card(self, label, value):
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)
        val_label = QLabel(value)
        val_label.setObjectName("statValue")
        val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(val_label)
        text_label = QLabel(label)
        text_label.setObjectName("statLabel")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(text_label)
        card._val_label = val_label
        return card

    def _create_application_card(self, app, index=None):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(85)
        card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(255, 255, 255, 160);
                border: 1px solid rgba(255, 255, 255, 220);
                border-radius: 12px;
                padding: 12px 16px;
            }
            QFrame#card:hover {
                border-color: rgba(96, 165, 250, 150);
                background-color: rgba(255, 255, 255, 200);
            }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(16)

        if index is not None:
            idx_label = QLabel(f"{index}-")
            idx_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #a78bfa; background: transparent;")
            card_layout.addWidget(idx_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        comp_label = QLabel(app.company_name)
        comp_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        comp_label.setCursor(Qt.CursorShape.IBeamCursor)
        comp_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #8b5cf6; background: transparent;")
        info_layout.addWidget(comp_label)

        pos_label = QLabel(app.position)
        pos_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #a78bfa; background: transparent;")
        info_layout.addWidget(pos_label)
        
        card_layout.addLayout(info_layout)
        card_layout.addStretch()

        date_label = QLabel(app.application_date)
        date_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #a78bfa; background: transparent;")
        card_layout.addWidget(date_label)

        badge = StatusBadge(app.status)
        card_layout.addWidget(badge)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        actions_layout.setContentsMargins(12, 0, 0, 0)

        edit_btn = QPushButton("Düzenle")
        edit_btn.setFixedHeight(32)
        edit_btn.setFixedWidth(68)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(96, 165, 250, 20);
                color: #60a5fa;
                border: 1px solid rgba(96, 165, 250, 40);
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 4px;
            }
            QPushButton:hover {
                background-color: rgba(96, 165, 250, 40);
                border-color: rgba(96, 165, 250, 70);
            }
        """)
        edit_btn.clicked.connect(lambda checked, a=app: self._edit_application(a))
        actions_layout.addWidget(edit_btn)

        del_btn = QPushButton("Sil")
        del_btn.setFixedHeight(32)
        del_btn.setFixedWidth(60)
        del_btn.setObjectName("dangerBtn")
        del_btn.setStyleSheet("padding: 2px 4px; font-size: 11px;")
        del_btn.clicked.connect(lambda checked, a=app: self._delete_application(a))
        actions_layout.addWidget(del_btn)

        card_layout.addLayout(actions_layout)
        return card

    def _load_data(self, apps=None):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if apps is None:
            apps = self._service.get_all()

        sort_type = self._sort_combo.currentData()
        if sort_type == "alpha_asc":
            apps.sort(key=lambda x: (x.company_name or "").lower())
        elif sort_type == "alpha_desc":
            apps.sort(key=lambda x: (x.company_name or "").lower(), reverse=True)
        elif sort_type == "date_asc":
            apps.sort(key=lambda x: x.application_date or "")
        elif sort_type == "created_asc":
            apps.sort(key=lambda x: x.id)
        elif sort_type == "created_desc":
            apps.sort(key=lambda x: x.id, reverse=True)
        else: # date_desc
            apps.sort(key=lambda x: x.application_date or "", reverse=True)

        all_apps = self._service.get_all()
        index_map = {a.id: idx for idx, a in enumerate(all_apps, start=1)}

        if not apps:
            empty_label = QLabel("Henüz başvuru bulunmuyor.")
            empty_label.setStyleSheet("color: #a78bfa; font-size: 14px; padding: 40px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(empty_label)
        else:
            for app in apps:
                idx = index_map.get(app.id, 0)
                card = self._create_application_card(app, idx)
                self._list_layout.addWidget(card)

        self._update_stats()
        self.data_changed.emit()

    def _update_stats(self):
        stats = self._service.get_stats()
        self._total_label._val_label.setText(str(stats["total"]))
        self._companies_label._val_label.setText(str(stats["unique_companies"]))
        
        while self._daily_layout.count():
            item = self._daily_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        for i, (day, count) in enumerate(stats.get("daily", [])):
            lbl = QLabel(f"<b>{day}</b>: {count} başvuru")
            border = "border-right: 1px solid rgba(139, 92, 246, 40);" if (i % 5) != 4 else "border: none;"
            lbl.setStyleSheet(f"font-size: 13px; color: #8b5cf6; background: transparent; padding: 2px 12px; {border}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            row = i // 5
            col = i % 5
            self._daily_layout.addWidget(lbl, row, col)

    def _add_application(self):
        company_names = list({a.company_name for a in self._service.get_all()})
        dialog = ApplicationDialog(parent=self, company_names=company_names)
        if dialog.exec():
            data = dialog.get_data()
            if not data["company_name"]:
                QMessageBox.warning(self, "Uyarı", "Şirket adı zorunludur.")
                return
            self._service.create(**data)
            self._load_data()

    def _edit_application(self, app):
        company_names = list({a.company_name for a in self._service.get_all()})
        dialog = ApplicationDialog(app=app, parent=self, company_names=company_names)
        if dialog.exec():
            data = dialog.get_data()
            app.company_name = data["company_name"]
            app.position = data["position"]
            app.status = data["status"]
            app.application_date = data["application_date"]
            self._service.update(app)
            self._load_data()

    def _delete_application(self, app):
        reply = QMessageBox.question(
            self, "Başvuruyu Sil",
            f"'{app.company_name} - {app.position}' başvurusunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete(app.id)
            self._load_data()

    def _on_search(self, text):
        if text.strip():
            apps = self._service.search(text.strip())
        else:
            apps = self._service.get_all()
        self._load_data(apps)

    def _on_filter(self, index):
        status = self._filter.currentData()
        if status == "all":
            apps = self._service.get_all()
        else:
            apps = self._service.filter_by_status(status)
        self._load_data(apps)
        
    def _open_date_filter(self):
        # Fetch all unique dates that have applications
        all_apps = self._service.get_all()
        active_dates = {app.application_date for app in all_apps if app.application_date}
        
        dialog = DateFilterDialog(active_dates, self)
        if dialog.exec() and dialog.selected_date:
            self._search.clear()
            self._filter.setCurrentIndex(0)
            
            filtered_apps = [app for app in all_apps if app.application_date == dialog.selected_date]
            self._load_data(filtered_apps)
            self._clear_filter_btn.show()

    def _clear_filters(self):
        self._search.clear()
        self._filter.setCurrentIndex(0)
        self._load_data()
        self._clear_filter_btn.hide()
