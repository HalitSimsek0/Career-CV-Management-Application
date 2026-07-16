from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QScrollArea, QComboBox,
)
from PyQt6.QtCore import Qt
from services.planned_company_service import PlannedCompanyService


class PlannedCompaniesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = PlannedCompanyService()
        from services.application_service import ApplicationService
        self._app_service = ApplicationService()
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        title = QLabel("Son Olarak Başvurulması Planlananlar")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # Stat card
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)
        self._count_card = self._create_stat_card("Planlanan Şirket", "0")
        stat_row.addWidget(self._count_card)
        stat_row.addStretch()
        layout.addLayout(stat_row)

        # Add company input area
        add_row = QHBoxLayout()
        add_row.setSpacing(10)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Şirket adı girin...")
        self._input.setMinimumHeight(42)
        self._input.setStyleSheet("""
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
        self._input.returnPressed.connect(self._add_company)
        add_row.addWidget(self._input)

        add_btn = QPushButton("+ Ekle")
        add_btn.setObjectName("primaryBtn")
        add_btn.setMinimumWidth(100)
        add_btn.setMinimumHeight(42)
        add_btn.clicked.connect(self._add_company)
        add_row.addWidget(add_btn)

        layout.addLayout(add_row)

        # Search & Sort row
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        
        self._search = QLineEdit()
        self._search.setPlaceholderText("Ara...")
        self._search.setMinimumWidth(150)
        self._search.textChanged.connect(self._on_search)
        search_row.addWidget(self._search)
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("Tümü", "all")
        self._filter_combo.addItem("Tamamlananlar", "completed")
        self._filter_combo.addItem("Bekleyenler", "pending")
        self._filter_combo.currentIndexChanged.connect(lambda x: self._load_data())
        search_row.addWidget(self._filter_combo)
        
        self._sort_combo = QComboBox()
        self._sort_combo.addItem("Eklenme Tarihi (Yeni-Eski)", "date_desc")
        self._sort_combo.addItem("Eklenme Tarihi (Eski-Yeni)", "date_asc")
        self._sort_combo.addItem("Alfabeye Göre (A-Z)", "alpha_asc")
        self._sort_combo.addItem("Alfabeye Göre (Z-A)", "alpha_desc")
        self._sort_combo.currentIndexChanged.connect(lambda x: self._load_data())
        search_row.addWidget(self._sort_combo)
        
        layout.addLayout(search_row)

        # Scroll area for company cards
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
        self._list_layout.setSpacing(8)
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

    def _create_company_card(self, company, index=None, app_count=0):
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(85)
        card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(255, 255, 255, 160);
                border: 1px solid rgba(255, 255, 255, 220);
                border-radius: 12px;
                padding: 8px 16px;
            }
            QFrame#card:hover {
                border-color: rgba(96, 165, 250, 150);
                background-color: rgba(255, 255, 255, 200);
            }
        """)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(12, 8, 12, 8)
        card_layout.setSpacing(12)

        if index is not None:
            idx_label = QLabel(f"{index}-")
            idx_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #a78bfa; background: transparent;")
            card_layout.addWidget(idx_label)

        # Company name
        name_label = QLabel(company.company_name)
        name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        name_label.setCursor(Qt.CursorShape.IBeamCursor)
        name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #8b5cf6;
            background: transparent;
        """)
        card_layout.addWidget(name_label)

        # Date
        if company.created_at:
            date_str = company.created_at[:10]  # yyyy-mm-dd
            date_label = QLabel(date_str)
            date_label.setStyleSheet("""
                font-size: 11px;
                color: #a78bfa;
                background: transparent;
            """)
            card_layout.addWidget(date_label)

        card_layout.addStretch()

        if company.is_applied is not None:
            is_applied_ui = company.is_applied
        else:
            is_applied_ui = (app_count > 0)
            
        toggle_btn = QPushButton()
        toggle_btn.setFixedSize(32, 32)
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_applied_ui:
            toggle_btn.setText("✓")
            toggle_btn.setStyleSheet("color: #10b981; font-weight: bold; font-size: 24px; padding: 0px; margin: 0px; border: none; background: transparent;")
            toggle_btn.setToolTip("Başvuruldu (Tıklayarak değiştirebilirsiniz)")
        else:
            toggle_btn.setText("✗")
            toggle_btn.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 24px; padding: 0px; margin: 0px; border: none; background: transparent;")
            toggle_btn.setToolTip("Başvurulmadı (Tıklayarak değiştirebilirsiniz)")
            
        def toggle_status(checked=False, c=company, current_ui_state=is_applied_ui):
            c.is_applied = not current_ui_state
            self._service.update(c)
            self._load_data()
            
        toggle_btn.clicked.connect(toggle_status)
        card_layout.addWidget(toggle_btn)

        if app_count > 0:
            applied_label = QLabel(str(app_count))
            applied_label.setStyleSheet("""
                font-size: 14px;
                font-weight: bold;
                color: #10b981;
                margin-right: 8px;
                background: transparent;
            """)
            card_layout.addWidget(applied_label)

        # Delete button
        del_btn = QPushButton("Sil")
        del_btn.setFixedHeight(32)
        del_btn.setFixedWidth(60)
        del_btn.setObjectName("dangerBtn")
        del_btn.setStyleSheet("padding: 2px 4px; font-size: 11px;")
        del_btn.clicked.connect(lambda checked, c=company: self._delete_company(c))
        card_layout.addWidget(del_btn)

        return card

    def _load_data(self, companies=None):
        # Clear existing cards
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if companies is None:
            if hasattr(self, '_search') and self._search.text().strip():
                companies = self._service.search(self._search.text().strip())
            else:
                companies = self._service.get_all()

        from utils.string_utils import search_normalize
        applied_apps = self._app_service.get_all()
        applied_counts = {}
        for app in applied_apps:
            if app.company_name:
                norm_name = search_normalize(app.company_name)
                applied_counts[norm_name] = applied_counts.get(norm_name, 0) + 1

        if hasattr(self, '_filter_combo'):
            filter_type = self._filter_combo.currentData()
            if filter_type != "all":
                filtered_companies = []
                for c in companies:
                    if c.is_applied is not None:
                        is_applied = c.is_applied
                    else:
                        norm_name = search_normalize(c.company_name) if c.company_name else ""
                        is_applied = (applied_counts.get(norm_name, 0) > 0)
                    
                    if filter_type == "completed" and is_applied:
                        filtered_companies.append(c)
                    elif filter_type == "pending" and not is_applied:
                        filtered_companies.append(c)
                companies = filtered_companies

        if hasattr(self, '_sort_combo'):
            sort_type = self._sort_combo.currentData()
            if sort_type == "alpha_asc":
                companies.sort(key=lambda x: (x.company_name or "").lower())
            elif sort_type == "alpha_desc":
                companies.sort(key=lambda x: (x.company_name or "").lower(), reverse=True)
            elif sort_type == "date_asc":
                companies.sort(key=lambda x: x.created_at or "")
            else: # date_desc
                companies.sort(key=lambda x: x.created_at or "", reverse=True)

        all_companies = self._service.get_all()
        index_map = {c.id: idx for idx, c in enumerate(all_companies, start=1)}

        if not companies:
            empty_label = QLabel("Bulunamadı." if hasattr(self, '_search') and self._search.text().strip() else "Henüz planlanan şirket eklenmedi.")
            empty_label.setStyleSheet("""
                color: #a78bfa;
                font-size: 14px;
                padding: 40px;
            """)
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(empty_label)
        else:
            for company in companies:
                idx = index_map.get(company.id, 0)
                norm_name = search_normalize(company.company_name) if company.company_name else ""
                app_count = applied_counts.get(norm_name, 0)
                card = self._create_company_card(company, idx, app_count)
                self._list_layout.addWidget(card)

        self._update_stats()

    def _update_stats(self):
        all_companies = self._service.get_all()
        total_count = len(all_companies)
        
        from utils.string_utils import search_normalize
        applied_apps = self._app_service.get_all()
        applied_counts = {}
        for app in applied_apps:
            if app.company_name:
                norm_name = search_normalize(app.company_name)
                applied_counts[norm_name] = applied_counts.get(norm_name, 0) + 1
        
        completed_count = 0
        for c in all_companies:
            if c.is_applied is not None:
                is_applied = c.is_applied
            else:
                norm_name = search_normalize(c.company_name) if c.company_name else ""
                is_applied = (applied_counts.get(norm_name, 0) > 0)
            if is_applied:
                completed_count += 1
                
        self._count_card._val_label.setText(f"{completed_count}/{total_count}")

    def _add_company(self):
        text = self._input.text().strip()
        if not text:
            QMessageBox.warning(self, "Uyarı", "Şirket adı boş olamaz.")
            return

        try:
            # Virgülle ayrılmış birden fazla şirket girilmiş olabilir
            names = [n.strip() for n in text.split(',') if n.strip()]
            added_count = 0
            duplicate_names = []
            
            for name in names:
                try:
                    self._service.create(name)
                    added_count += 1
                except ValueError as e:
                    if "zaten planlananlar listesinde var" in str(e):
                        duplicate_names.append(name)
                    else:
                        raise e
                
            self._input.clear()
            self._load_data()
            
            if duplicate_names:
                if added_count > 0:
                    msg = f"{added_count} şirket başarıyla eklendi.\nAncak aşağıdaki şirketler zaten listede olduğu için eklenmedi:\n" + ", ".join(duplicate_names)
                else:
                    msg = "Girdiğiniz şirketler zaten listede mevcut:\n" + ", ".join(duplicate_names)
                QMessageBox.information(self, "Bilgi", msg)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _delete_company(self, company):
        reply = QMessageBox.question(
            self, "Şirketi Sil",
            f"'{company.company_name}' şirketini listeden silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._service.delete(company.id)
            self._load_data()

    def _on_search(self, text):
        self._load_data()
