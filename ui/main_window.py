from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
)
from PyQt6.QtCore import Qt
from ui.style_manager import StyleManager
from ui.pages.cv_upload_page import CVUploadPage
from ui.pages.applications_page import ApplicationsPage
from ui.pages.stats_page import StatsPage
from ui.pages.planned_companies_page import PlannedCompaniesPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CV Manager")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self.setStyleSheet(StyleManager.get_theme())
        self._current_nav_idx = 0
        self._nav_buttons = []
        self._setup_ui()
        self._navigate(0)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(6)

        logo = QLabel("CV Manager")
        logo.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #60a5fa;
            padding: 10px 8px 20px 8px;
        """)
        sidebar_layout.addWidget(logo)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(12)

        nav_items = [
            ("CV Yönetimi", 0),
            ("PDF Düzenleyici", 1),
            ("İlan Analizi", 2),
            ("Başvurularım", 3),
            ("İstatistikler", 4),
            ("Planlananlar", 5),
        ]
        for text, idx in nav_items:
            btn = QPushButton(f"  {text}")
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #a78bfa; font-size: 11px; padding: 8px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        self._stack = QStackedWidget()
        content_wrapper = QVBoxLayout()
        content_wrapper.setContentsMargins(16, 16, 16, 16)
        content_wrapper.addWidget(self._stack)
        content_container = QWidget()
        content_container.setLayout(content_wrapper)
        main_layout.addWidget(content_container)

        self._cv_page = CVUploadPage()
        self._pdf_page = None
        self._job_page = None
        self._apps_page = ApplicationsPage()
        self._stats_page = StatsPage()
        self._planned_page = PlannedCompaniesPage()

        self._stack.addWidget(self._cv_page)
        self._stack.addWidget(QWidget()) # placeholder for pdf_page
        self._stack.addWidget(QWidget()) # placeholder for job_page
        self._stack.addWidget(self._apps_page)
        self._stack.addWidget(self._stats_page)
        self._stack.addWidget(self._planned_page)

        self._cv_page.edit_requested.connect(self._open_pdf_editor)
        self._apps_page.data_changed.connect(self._stats_page._refresh_data)

    def _navigate(self, index):
        if index == 1 and self._pdf_page is None:
            from ui.pages.pdf_editor_page import PDFEditorPage
            self._pdf_page = PDFEditorPage()
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            self._stack.insertWidget(1, self._pdf_page)
            w.deleteLater()
            
        if index == 2 and self._job_page is None:
            from ui.pages.job_analysis_page import JobAnalysisPage
            self._job_page = JobAnalysisPage()
            w = self._stack.widget(2)
            self._stack.removeWidget(w)
            self._stack.insertWidget(2, self._job_page)
            w.deleteLater()

        self._current_nav_idx = index
        self._stack.setCurrentIndex(index)
        
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setObjectName("navBtnActive")
            else:
                btn.setObjectName("navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Defer data refresh to avoid UI stutter on tab switch
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(10, self._defer_load)

    def _defer_load(self):
        widget = self._stack.currentWidget()
        if hasattr(widget, '_load_data'):
            widget._load_data()
        if hasattr(widget, '_refresh_data'):
            widget._refresh_data()

    def _open_pdf_editor(self, file_path):
        self._navigate(1)
        self._pdf_page.load_pdf(file_path)
