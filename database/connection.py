import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR

logger = logging.getLogger(__name__)


class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._conn = None
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            # Set a timeout of 5 seconds to handle concurrent access blocks safely
            self._conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=5.0)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=5000")
        return self._conn

    def is_healthy(self) -> bool:
        """Check if the database connection is alive and responding."""
        if self._conn is None:
            return False
        try:
            self._conn.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error as e:
                logger.warning("DB kapatılırken hata oluştu: %s", e)
            finally:
                self._conn = None

    def backup(self):
        if DB_PATH.exists():
            try:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = BACKUP_DIR / f"cv_manager_backup_{ts}.db"
                shutil.copy2(str(DB_PATH), str(dest))
                self._cleanup_old_backups()
                return dest
            except Exception as e:
                logger.error("Veritabanı yedekleme hatası: %s", e)
                return None
        return None

    def _cleanup_old_backups(self, keep=5):
        try:
            backups = sorted(BACKUP_DIR.glob("cv_manager_backup_*.db"), reverse=True)
            for old in backups[keep:]:
                old.unlink(missing_ok=True)
        except Exception as e:
            logger.warning("Eski yedekler temizlenirken hata oluştu: %s", e)
