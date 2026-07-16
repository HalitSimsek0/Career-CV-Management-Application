import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from database.migrations import run_migrations
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    run_migrations()
    
    # Program açılırken not defterini güncelle
    from services.application_service import ApplicationService
    ApplicationService()._sync_backup_txt()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
