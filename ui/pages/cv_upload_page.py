from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QScrollArea, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.cv_parse_service import CVParseService
from models.cv_snapshot import CVSnapshot


class CVUploadPage(QWidget):
    edit_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = CVParseService()
        self._current_cv = None
        self._setup_ui()
        self._load_latest()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("CV Yönetimi")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        self._edit_btn = QPushButton("PDF Düzenle")
        self._edit_btn.setMinimumWidth(120)
        self._edit_btn.clicked.connect(self._request_edit)
        self._edit_btn.hide()
        header.addWidget(self._edit_btn)

        upload_btn = QPushButton("+ CV Yükle")
        upload_btn.setObjectName("primaryBtn")
        upload_btn.setMinimumWidth(140)
        upload_btn.clicked.connect(self._upload_cv)
        header.addWidget(upload_btn)
        layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(16)
        scroll.setWidget(self._content_widget)
        layout.addWidget(scroll)

        self._empty_label = QLabel("Henüz CV yüklenmedi.\n\nYeni bir CV yüklemek için sağ üstteki butonu kullanın.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #a78bfa; font-size: 15px; padding: 40px;")
        self._content_layout.addWidget(self._empty_label)
        self._content_layout.addStretch()

    def _load_latest(self):
        cv = self._service.get_latest_cv()
        if cv:
            self._display_cv(cv)

    def _upload_cv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "CV Seç", "", "PDF veya Word (*.pdf *.docx)"
        )
        if file_path:
            try:
                cv = self._service.parse_file(file_path)
                self._display_cv(cv)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"CV yüklenirken hata oluştu:\n{str(e)}")

    def _request_edit(self):
        if self._current_cv and self._current_cv.file_path.lower().endswith('.pdf'):
            self.edit_requested.emit(self._current_cv.file_path)
        else:
            QMessageBox.information(self, "Bilgi", "Sadece PDF formatındaki CV'ler düzenlenebilir.")

    def _display_cv(self, cv: CVSnapshot):
        self._current_cv = cv

        if cv.file_path.lower().endswith('.pdf'):
            self._edit_btn.show()
        else:
            self._edit_btn.hide()

        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        header_card = QFrame()
        header_card.setObjectName("card")
        h_layout = QVBoxLayout(header_card)
        
        name_row = QHBoxLayout()
        name_label = QLabel(cv.full_name or "İsimsiz Aday")
        name_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #60a5fa; background: transparent;")
        name_row.addWidget(name_label)
        name_row.addStretch()
        
        self._delete_cv_btn = QPushButton("CV'yi Sil")
        self._delete_cv_btn.setObjectName("dangerBtn")
        self._delete_cv_btn.clicked.connect(self._delete_cv)
        name_row.addWidget(self._delete_cv_btn)
        h_layout.addLayout(name_row)

        contact_info = []
        if cv.email: contact_info.append(f"📧 {cv.email}")
        if cv.phone: contact_info.append(f"📱 {cv.phone}")
        if cv.location: contact_info.append(f"📍 {cv.location}")
        if contact_info:
            c_label = QLabel("  |  ".join(contact_info))
            c_label.setStyleSheet("color: #8b5cf6; font-size: 16px; background: transparent;")
            h_layout.addWidget(c_label)

        links_info = []
        if cv.linkedin_url:
            url = cv.linkedin_url if cv.linkedin_url.startswith("http") else f"https://{cv.linkedin_url}"
            links_info.append(f'🔗 <a href="{url}" style="color: #60a5fa; text-decoration: none;">{cv.linkedin_url}</a>')
        if cv.github_url:
            url = cv.github_url if cv.github_url.startswith("http") else f"https://{cv.github_url}"
            links_info.append(f'💻 <a href="{url}" style="color: #60a5fa; text-decoration: none;">{cv.github_url}</a>')
        if cv.website_url:
            url = cv.website_url if cv.website_url.startswith("http") else f"https://{cv.website_url}"
            links_info.append(f'🌐 <a href="{url}" style="color: #60a5fa; text-decoration: none;">{cv.website_url}</a>')
        
        if links_info:
            l_label = QLabel("  |  ".join(links_info))
            l_label.setOpenExternalLinks(True)
            l_label.setTextFormat(Qt.TextFormat.RichText)
            l_label.setStyleSheet("font-size: 16px; background: transparent;")
            h_layout.addWidget(l_label)

        self._content_layout.addWidget(header_card)

        if cv.summary:
            sum_card = QFrame()
            sum_card.setObjectName("card")
            s_layout = QVBoxLayout(sum_card)
            s_title = QLabel("Özet")
            s_title.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 18px; background: transparent;")
            s_layout.addWidget(s_title)
            s_text = QLabel(cv.summary)
            s_text.setWordWrap(True)
            s_text.setTextFormat(Qt.TextFormat.RichText)
            s_text.setStyleSheet("color: #8b5cf6; font-size: 16px; background: transparent;")
            s_layout.addWidget(s_text)
            self._content_layout.addWidget(sum_card)

        if cv.skills:
            sk_card = QFrame()
            sk_card.setObjectName("card")
            sk_layout = QVBoxLayout(sk_card)
            sk_title = QLabel("Yetenekler")
            sk_title.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 18px; background: transparent;")
            sk_layout.addWidget(sk_title)

            tags_widget = QWidget()
            tags_layout = QHBoxLayout(tags_widget)
            tags_layout.setContentsMargins(0, 0, 0, 0)
            tags_layout.setSpacing(8)

            current_row = QWidget()
            row_layout = QHBoxLayout(current_row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            sk_layout.addWidget(current_row)

            for i, skill in enumerate(cv.skills):
                tag = QLabel(skill)
                tag.setStyleSheet("""
                    QLabel {
                        background-color: rgba(96, 165, 250, 20);
                        color: #60a5fa;
                        border: 1px solid rgba(96, 165, 250, 40);
                        border-radius: 12px;
                        padding: 6px 14px;
                        font-weight: 600;
                        font-size: 14px;
                    }
                """)
                row_layout.addWidget(tag)
                if (i + 1) % 6 == 0:
                    row_layout.addStretch()
                    current_row = QWidget()
                    row_layout = QHBoxLayout(current_row)
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    sk_layout.addWidget(current_row)

            row_layout.addStretch()
            self._content_layout.addWidget(sk_card)

        def add_section(title, items):
            if not items: return
            card = QFrame()
            card.setObjectName("card")
            layout = QVBoxLayout(card)
            lbl = QLabel(title)
            lbl.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 18px; background: transparent;")
            layout.addWidget(lbl)

            for item in items:
                if isinstance(item, dict):
                    t_val = item.get('title', '')
                    if not t_val.strip().startswith('•') and not t_val.strip().startswith('<span'):
                        t_val = f"• {t_val}"
                    t = QLabel(t_val)
                    t.setWordWrap(True)
                    t.setTextFormat(Qt.TextFormat.RichText)
                    t.setStyleSheet("color: #8b5cf6; font-size: 16px; background: transparent;")
                    layout.addWidget(t)
                    for detail in item.get('details', []):
                        d_val = detail
                        if not d_val.strip().startswith('-') and not d_val.strip().startswith('<span'):
                            d_val = f"   - {d_val}"
                        d = QLabel(d_val)
                        d.setWordWrap(True)
                        d.setTextFormat(Qt.TextFormat.RichText)
                        d.setStyleSheet("color: #8b5cf6; font-size: 15px; background: transparent;")
                        layout.addWidget(d)
                else:
                    t_val = item
                    if not str(t_val).strip().startswith('•') and not str(t_val).strip().startswith('<span'):
                        t_val = f"• {t_val}"
                    t = QLabel(t_val)
                    t.setWordWrap(True)
                    t.setTextFormat(Qt.TextFormat.RichText)
                    t.setStyleSheet("color: #8b5cf6; font-size: 15px; background: transparent;")
                    layout.addWidget(t)
            self._content_layout.addWidget(card)

        add_section("Deneyim", cv.experiences)
        add_section("Eğitim", cv.education)
        add_section("Projeler", cv.projects)
        add_section("Diller", cv.languages)
        add_section("Sertifikalar", cv.certifications)
        add_section("Gönüllü Çalışmalar", getattr(cv, "volunteer", []))
        add_section("Referanslar", getattr(cv, "references", []))
        add_section("Kişisel Bilgiler", getattr(cv, "personal_info", []))

        self._content_layout.addStretch()

    def _delete_cv(self):
        if not self._current_cv:
            return
        reply = QMessageBox.question(self, "Onay", "Bu CV'yi silmek istediğinize emin misiniz?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._service.delete_cv(self._current_cv.id)
                self._current_cv = None
                self._load_latest()
                if not self._current_cv:
                    # Clear layout
                    while self._content_layout.count():
                        item = self._content_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                    self._empty_label = QLabel("Henüz CV yüklenmedi.\n\nYeni bir CV yüklemek için sağ üstteki butonu kullanın.")
                    self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._empty_label.setStyleSheet("color: #a78bfa; font-size: 15px; padding: 40px;")
                    self._content_layout.addWidget(self._empty_label)
                    self._content_layout.addStretch()
                    self._edit_btn.hide()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Silinirken hata oluştu: {e}")
