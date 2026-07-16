class StyleManager:
    LIGHT_THEME = """
        QMainWindow {
            background-color: #faf5ff;
        }
        QWidget#central {
            background-color: #faf5ff;
        }
        QWidget {
            background-color: #faf5ff;
            color: #a78bfa;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            font-size: 14px;
        }
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        QScrollArea > QWidget > QWidget {
            background-color: transparent;
        }
        QLabel {
            color: #a78bfa;
            background: transparent;
        }
        QLabel#sectionTitle {
            font-size: 24px;
            font-weight: 700;
            color: #8b5cf6;
            padding: 8px 0;
        }
        QLabel#statValue {
            font-size: 36px;
            font-weight: 800;
            color: #60a5fa;
        }
        QLabel#statLabel {
            font-size: 13px;
            font-weight: 600;
            color: #a78bfa;
        }
        QPushButton {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #e0e7ff;
            border-radius: 12px;
            padding: 10px 20px;
            font-weight: 600;
            min-height: 40px;
        }
        QPushButton:hover {
            background-color: #eff6ff;
            border-color: #c7d2fe;
            color: #8b5cf6;
        }
        QPushButton:pressed {
            background-color: #e0e7ff;
        }
        QPushButton#primaryBtn {
            background-color: #60a5fa;
            color: #ffffff;
            border: none;
            font-weight: 600;
            border-radius: 12px;
            padding: 10px 20px;
        }
        QPushButton#primaryBtn:hover {
            background-color: #93c5fd;
        }
        QPushButton#primaryBtn:pressed {
            background-color: #bfdbfe;
        }
        QPushButton#dangerBtn {
            background-color: #fdf2f8;
            color: #f472b6;
            border: 1px solid #fce7f3;
            font-weight: 600;
            border-radius: 12px;
        }
        QPushButton#dangerBtn:hover {
            background-color: #fce7f3;
            border-color: #fbcfe8;
        }
        QPushButton#dangerBtn:pressed {
            background-color: #fce7f3;
        }
        QPushButton#navBtn {
            background: transparent;
            border: none;
            border-radius: 12px;
            padding: 12px 16px;
            text-align: left;
            font-size: 14px;
            color: #8b5cf6;
            min-height: 44px;
            font-weight: 600;
        }
        QPushButton#navBtn:hover {
            background-color: #eff6ff;
            color: #8b5cf6;
        }
        QPushButton#navBtnActive {
            background-color: #eff6ff;
            border: none;
            border-left: 4px solid #60a5fa;
            border-radius: 0 12px 12px 0;
            padding: 12px 16px;
            text-align: left;
            font-size: 14px;
            font-weight: 700;
            color: #60a5fa;
            min-height: 44px;
        }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            padding: 12px 16px;
            selection-background-color: #bfdbfe;
            selection-color: #8b5cf6;
            font-size: 14px;
        }
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #60a5fa;
            padding: 11px 15px;
            background-color: #ffffff;
        }
        QLineEdit::placeholder, QTextEdit::placeholder, QPlainTextEdit::placeholder {
            color: #c4b5fd;
        }
        QComboBox {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            padding: 10px 16px;
            min-height: 28px;
            font-size: 14px;
        }
        QComboBox:hover {
            border-color: #c4b5fd;
        }
        QComboBox:focus {
            border: 2px solid #60a5fa;
            padding: 9px 15px;
        }
        QComboBox::drop-down {
            border: none;
            width: 34px;
        }
        QComboBox::down-arrow {
            image: none;
            width: 0px;
            height: 0px;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #a78bfa;
            margin-right: 12px;
        }
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #c7d2fe;
            selection-background-color: #eff6ff;
            selection-color: #60a5fa;
            border-radius: 12px;
            padding: 4px;
        }
        QTableWidget {
            background-color: #ffffff;
            color: #a78bfa;
            gridline-color: #eff6ff;
            border: 1px solid #e0e7ff;
            border-radius: 16px;
            selection-background-color: #eff6ff;
            selection-color: #60a5fa;
            font-size: 14px;
        }
        QTableWidget::item {
            padding: 12px 16px;
            border-bottom: 1px solid #faf5ff;
        }
        QTableWidget::item:selected {
            background-color: #eff6ff;
            color: #60a5fa;
            font-weight: 600;
        }
        QHeaderView::section {
            background-color: #faf5ff;
            color: #8b5cf6;
            padding: 12px 16px;
            border: none;
            border-bottom: 2px solid #e0e7ff;
            font-weight: 700;
            font-size: 13px;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            border-radius: 12px;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            background: #c7d2fe;
            border-radius: 12px;
            min-height: 40px;
        }
        QScrollBar::handle:vertical:hover {
            background: #c4b5fd;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar:horizontal {
            background: transparent;
            height: 10px;
            border-radius: 12px;
            margin: 2px;
        }
        QScrollBar::handle:horizontal {
            background: #c7d2fe;
            border-radius: 12px;
            min-width: 40px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #c4b5fd;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0;
        }
        QTabWidget::pane {
            border: 1px solid #e0e7ff;
            border-radius: 16px;
            background: #ffffff;
            top: -1px;
        }
        QTabBar::tab {
            background: transparent;
            color: #a78bfa;
            padding: 12px 24px;
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 600;
            font-size: 14px;
            margin-right: 8px;
        }
        QTabBar::tab:selected {
            color: #60a5fa;
            border-bottom: 3px solid #60a5fa;
            background: #ffffff;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }
        QTabBar::tab:hover {
            color: #a78bfa;
            background: #faf5ff;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }
        QGroupBox {
            border: 1px solid #e0e7ff;
            border-radius: 16px;
            margin-top: 16px;
            padding: 16px;
            font-weight: 700;
            color: #8b5cf6;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 12px;
            color: #8b5cf6;
        }
        QSplitter::handle {
            background: #e0e7ff;
            width: 2px;
        }
        QToolTip {
            background-color: #ffffff;
            color: #8b5cf6;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            padding: 8px 12px;
            font-size: 13px;
        }
        QFrame#sidebar {
            background-color: #ffffff;
            border-right: 1px solid #e0e7ff;
        }
        QFrame#card {
            background-color: #ffffff;
            border: 1px solid #e0e7ff;
            border-radius: 16px;
            padding: 24px;
        }
        QFrame#statCard {
            background-color: #ffffff;
            border: 1px solid #e0e7ff;
            border-radius: 16px;
            padding: 20px;
        }
        QFrame#separator {
            background-color: #e0e7ff;
            max-height: 1px;
        }
        QProgressBar {
            background-color: #eff6ff;
            border: none;
            border-radius: 12px;
            text-align: center;
            color: transparent;
            min-height: 16px;
        }
        QProgressBar::chunk {
            background-color: #60a5fa;
            border-radius: 12px;
        }
        QDateEdit {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            padding: 10px 16px;
            font-size: 14px;
        }
        QDateEdit:focus {
            border: 2px solid #60a5fa;
            padding: 9px 15px;
        }
        QDateEdit::drop-down {
            border: none;
            width: 34px;
        }
        QCalendarWidget {
            background-color: #ffffff;
        }
        QMenu {
            background-color: #ffffff;
            color: #a78bfa;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            padding: 8px;
        }
        QMenu::item {
            padding: 10px 32px;
            border-radius: 12px;
            font-weight: 600;
        }
        QMenu::item:selected {
            background-color: #eff6ff;
            color: #60a5fa;
        }
        QStatusBar {
            background-color: #ffffff;
            color: #a78bfa;
            border-top: 1px solid #e0e7ff;
            font-weight: 500;
            padding: 4px;
        }
        QDialog {
            background-color: #faf5ff;
        }
    """

    @staticmethod
    def get_theme() -> str:
        return StyleManager.LIGHT_THEME

    @staticmethod
    def get_status_color(status: str) -> str:
        from utils.skill_dictionary import STATUS_COLORS
        return STATUS_COLORS.get(status, "#6b7280")
