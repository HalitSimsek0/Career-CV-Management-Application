from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt
from services.job_analysis_service import JobAnalysisService


class JobAnalysisPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = JobAnalysisService()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("İş İlanı Analizi")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        input_label = QLabel("İş ilanı metnini yapıştırın (Türkçe veya İngilizce):")
        input_label.setStyleSheet("color: #c4b5fd; font-size: 12px;")
        layout.addWidget(input_label)

        self._input = QTextEdit()
        self._input.setPlaceholderText(
            "İş ilanı metnini buraya yapıştırın...\n\n"
            "Örnek: LinkedIn, Kariyer.net veya herhangi bir siteden\n"
            "ilanın metnini kopyalayıp buraya yapıştırın."
        )
        self._input.setMinimumHeight(160)
        self._input.setMaximumHeight(220)
        layout.addWidget(self._input)

        btn_row = QHBoxLayout()
        
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["Otomatik Algıla", "İngilizce (Zorla)", "Türkçe (Zorla)"])
        self._lang_combo.setMinimumHeight(32)
        btn_row.addWidget(self._lang_combo)
        
        analyze_btn = QPushButton("Analiz Et")
        analyze_btn.setObjectName("primaryBtn")
        analyze_btn.setMinimumWidth(160)
        analyze_btn.clicked.connect(self._analyze)
        btn_row.addWidget(analyze_btn)

        clear_btn = QPushButton("Temizle")
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._result_widget = QWidget()
        self._result_layout = QVBoxLayout(self._result_widget)
        self._result_layout.setSpacing(12)
        result_scroll.setWidget(self._result_widget)
        layout.addWidget(result_scroll)

        self._empty_label = QLabel("Analiz sonuçları burada görünecek")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #a78bfa; font-size: 15px; padding: 40px;")
        self._result_layout.addWidget(self._empty_label)
        self._result_layout.addStretch()

    def _analyze(self):
        text = self._input.toPlainText().strip()
        if not text:
            return
            
        force_lang = None
        combo_text = self._lang_combo.currentText()
        if combo_text == "İngilizce (Zorla)":
            force_lang = "en"
        elif combo_text == "Türkçe (Zorla)":
            force_lang = "tr"
            
        result = self._service.analyze(text, force_lang)
        self._display_results(result)

    def _display_results(self, result):
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        container = QFrame()
        container.setObjectName("card")
        grid = QGridLayout(container)
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        row = 0
        lang_display = "Türkçe 🇹🇷" if result["language"] == "tr" else "İngilizce 🇬🇧"
        row = self._add_result_row(grid, row, "Dil", lang_display)
        
        cv_match = result.get("cv_match_score", -1)
        if cv_match >= 0:
            score_color = "#10b981" if cv_match >= 70 else ("#f59e0b" if cv_match >= 40 else "#ef4444")
            score_display = f"<span style='color: {score_color}; font-size: 16px; font-weight: bold;'>%{cv_match}</span>"
            row = self._add_result_row(grid, row, "CV Uyum Skoru", score_display)

        fields = [
            ("Şirket Adı", result.get("company_name", "")),
            ("Pozisyon", result.get("position", "")),
            ("İstenen Deneyim", result.get("experience", "")),
            ("Eğitim", result.get("education", "")),
            ("Lokasyon", result.get("location", "")),
            ("Çalışma Tipi", result.get("work_type", "")),
            ("Maaş", result.get("salary", "")),
        ]
        for label, value in fields:
            if value:
                row = self._add_result_row(grid, row, label, value)

        self._result_layout.addWidget(container)

        matching_skills = result.get("matching_skills", [])
        missing_skills = result.get("missing_skills", [])
        
        if matching_skills or missing_skills:
            if matching_skills:
                skills_frame = QFrame()
                skills_frame.setObjectName("card")
                skills_layout = QVBoxLayout(skills_frame)
                skills_title = QLabel(f"Eşleşen Yetenekler ({len(matching_skills)})")
                skills_title.setStyleSheet("font-weight: bold; color: #10b981; font-size: 14px; background: transparent;")
                skills_layout.addWidget(skills_title)
                skills_layout.addWidget(self._create_tag_grid(matching_skills, "#10b981", "rgba(16, 185, 129, 15)", "rgba(16, 185, 129, 30)"))
                self._result_layout.addWidget(skills_frame)
                
            if missing_skills:
                miss_frame = QFrame()
                miss_frame.setObjectName("card")
                miss_layout = QVBoxLayout(miss_frame)
                miss_title = QLabel(f"Eksik Yetenekler ({len(missing_skills)})")
                miss_title.setStyleSheet("font-weight: bold; color: #ef4444; font-size: 14px; background: transparent;")
                miss_layout.addWidget(miss_title)
                miss_layout.addWidget(self._create_tag_grid(missing_skills, "#ef4444", "rgba(239, 68, 68, 15)", "rgba(239, 68, 68, 30)"))
                self._result_layout.addWidget(miss_frame)
        else:
            skills = result.get("required_skills", [])
            if skills:
                skills_frame = QFrame()
                skills_frame.setObjectName("card")
                skills_layout = QVBoxLayout(skills_frame)
                skills_title = QLabel(f"Teknik Yetenekler ({len(skills)})")
                skills_title.setStyleSheet("font-weight: bold; color: #0d9488; font-size: 14px; background: transparent;")
                skills_layout.addWidget(skills_title)
                skills_layout.addWidget(self._create_tag_grid(skills, "#0d9488", "rgba(13, 148, 136, 15)", "rgba(13, 148, 136, 30)"))
                self._result_layout.addWidget(skills_frame)

            soft_skills = result.get("soft_skills", [])
            if soft_skills:
                soft_frame = QFrame()
                soft_frame.setObjectName("card")
                soft_layout = QVBoxLayout(soft_frame)
                soft_title = QLabel(f"Sosyal Yetenekler ({len(soft_skills)})")
                soft_title.setStyleSheet("font-weight: bold; color: #8b5cf6; font-size: 14px; background: transparent;")
                soft_layout.addWidget(soft_title)
                soft_layout.addWidget(self._create_tag_grid(soft_skills, "#8b5cf6", "rgba(139, 92, 246, 15)", "rgba(139, 92, 246, 30)"))
                self._result_layout.addWidget(soft_frame)

        responsibilities = result.get("responsibilities", [])
        if responsibilities:
            resp_frame = QFrame()
            resp_frame.setObjectName("card")
            resp_layout = QVBoxLayout(resp_frame)
            resp_title = QLabel("Sorumluluklar")
            resp_title.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 14px; background: transparent;")
            resp_layout.addWidget(resp_title)
            for i, item in enumerate(responsibilities[:10], start=1):
                item_label = QLabel(f"{i}- {item}")
                item_label.setWordWrap(True)
                item_label.setStyleSheet("color: #8b5cf6; font-size: 12px; padding: 2px 0; background: transparent;")
                resp_layout.addWidget(item_label)
            self._result_layout.addWidget(resp_frame)

        benefits = result.get("benefits", [])
        if benefits:
            ben_frame = QFrame()
            ben_frame.setObjectName("card")
            ben_layout = QVBoxLayout(ben_frame)
            ben_title = QLabel("Yan Haklar")
            ben_title.setStyleSheet("font-weight: bold; color: #0891b2; font-size: 14px; background: transparent;")
            ben_layout.addWidget(ben_title)
            for i, item in enumerate(benefits[:10], start=1):
                item_label = QLabel(f"{i}- {item}")
                item_label.setWordWrap(True)
                item_label.setStyleSheet("color: #8b5cf6; font-size: 12px; padding: 2px 0; background: transparent;")
                ben_layout.addWidget(item_label)
            self._result_layout.addWidget(ben_frame)

        keywords = result.get("keywords", [])
        if keywords:
            kw_frame = QFrame()
            kw_frame.setObjectName("card")
            kw_layout = QVBoxLayout(kw_frame)
            kw_title = QLabel("Anahtar Kelimeler")
            kw_title.setStyleSheet("font-weight: bold; color: #d97706; font-size: 14px; background: transparent;")
            kw_layout.addWidget(kw_title)
            kw_layout.addWidget(self._create_tag_grid(keywords, "#d97706", "rgba(217, 119, 6, 15)", "rgba(217, 119, 6, 30)"))
            self._result_layout.addWidget(kw_frame)
            
        cover_letter = result.get("cover_letter", "")
        if cover_letter:
            cl_frame = QFrame()
            cl_frame.setObjectName("card")
            cl_layout = QVBoxLayout(cl_frame)
            cl_title = QLabel("Ön Yazı Taslağı")
            cl_title.setStyleSheet("font-weight: bold; color: #8b5cf6; font-size: 14px; background: transparent;")
            cl_layout.addWidget(cl_title)
            
            cl_edit = QTextEdit()
            cl_edit.setPlainText(cover_letter)
            cl_edit.setMinimumHeight(120)
            cl_edit.setStyleSheet("background-color: rgba(255, 255, 255, 10); color: #c4b5fd; font-size: 13px; border-radius: 8px;")
            cl_layout.addWidget(cl_edit)
            self._result_layout.addWidget(cl_frame)
            
        suggestions = result.get("suggestions", [])
        if suggestions:
            sug_frame = QFrame()
            sug_frame.setObjectName("card")
            sug_layout = QVBoxLayout(sug_frame)
            sug_title = QLabel("Aksiyon Önerileri")
            sug_title.setStyleSheet("font-weight: bold; color: #f59e0b; font-size: 14px; background: transparent;")
            sug_layout.addWidget(sug_title)
            
            for i, item in enumerate(suggestions, start=1):
                item_label = QLabel(f"{i}- 💡 {item}")
                item_label.setWordWrap(True)
                item_label.setStyleSheet("color: #fbbf24; font-size: 13px; padding: 4px; background: transparent;")
                sug_layout.addWidget(item_label)
            self._result_layout.addWidget(sug_frame)
            
        full_trans = result.get("full_translation", "")
        if full_trans:
            tr_frame = QFrame()
            tr_frame.setObjectName("card")
            tr_layout = QVBoxLayout(tr_frame)
            is_english = result.get("language") == "en"
            title_text = "İlanın Türkçe Çevirisi" if is_english else "İlan Metni (Orijinal)"
            tr_title = QLabel(title_text)
            tr_title.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 14px; background: transparent;")
            tr_layout.addWidget(tr_title)
            
            tr_text = QLabel(full_trans)
            tr_text.setWordWrap(True)
            tr_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            tr_text.setStyleSheet("color: #8b5cf6; font-size: 13px; background: transparent; padding: 4px;")
            tr_layout.addWidget(tr_text)
            self._result_layout.addWidget(tr_frame)

        self._result_layout.addStretch()

    def _add_result_row(self, grid, row, label, value):
        l = QLabel(label)
        l.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 13px; background: transparent;")
        v = QLabel(str(value))
        v.setWordWrap(True)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.setStyleSheet("font-size: 13px; color: #8b5cf6; background: transparent;")
        grid.addWidget(l, row, 0, Qt.AlignmentFlag.AlignTop)
        grid.addWidget(v, row, 1)
        return row + 1

    def _create_tag_grid(self, items, text_color, bg_color, border_color):
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 4, 0, 0)
        wrapper_layout.setSpacing(6)

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        for i, item in enumerate(items):
            tag = QLabel(str(item))
            tag.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 14px;
                    padding: 5px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }}
            """)
            row_layout.addWidget(tag)
            if (i + 1) % 6 == 0:
                row_layout.addStretch()
                wrapper_layout.addWidget(row_widget)
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(6)

        row_layout.addStretch()
        wrapper_layout.addWidget(row_widget)
        return wrapper

    def _clear(self):
        self._input.clear()
        while self._result_layout.count():
            item = self._result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._empty_label = QLabel("Analiz sonuçları burada görünecek")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #a78bfa; font-size: 15px; padding: 40px;")
        self._result_layout.addWidget(self._empty_label)
        self._result_layout.addStretch()
