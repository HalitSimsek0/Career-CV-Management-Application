import logging
from typing import Optional, List
import sqlite3
from repositories.base_repository import BaseRepository
from models.cv_snapshot import CVSnapshot

logger = logging.getLogger(__name__)


class CVRepository(BaseRepository):
    def __init__(self):
        super().__init__("cv_snapshots")

    def save(self, cv: CVSnapshot) -> int:
        # Sadece son CV'nin kalması için önce tüm geçmiş CV'leri siliyoruz
        self.clear_all(confirm=True)
        
        data = cv.to_dict()
        data.pop("id", None)
        columns = ", ".join(f'"{k}"' for k in data.keys())
        placeholders = ", ".join(["?"] * len(data))
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"INSERT INTO {self._table} ({columns}) VALUES ({placeholders})",
                list(data.values()),
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error("CV kaydedilirken veritabanı hatası: %s", e)
            self.conn.rollback()
            raise

    def update(self, cv: CVSnapshot) -> bool:
        if cv.id is None:
            return False
            
        data = cv.to_dict()
        data.pop("id", None)
        set_clause = ", ".join([f'"{k}" = ?' for k in data.keys()])
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE {self._table} SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
                list(data.values()) + [cv.id],
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error("CV güncellenirken veritabanı hatası (id=%s): %s", cv.id, e)
            self.conn.rollback()
            raise

    def get_by_id(self, cv_id: int) -> Optional[CVSnapshot]:
        row = self.find_by_id(cv_id)
        if row:
            return CVSnapshot.from_row(row)
        return None

    def get_all(self) -> List[CVSnapshot]:
        rows = self.find_all()
        return [CVSnapshot.from_row(r) for r in rows]

    def get_latest(self) -> Optional[CVSnapshot]:
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT * FROM {self._table} ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return CVSnapshot.from_row(row)
        return None

    def clear_all(self, confirm: bool = False):
        if not confirm:
            logger.warning("clear_all onay olmadan çağrıldı. İşlem iptal edildi.")
            raise ValueError("Tüm verileri silmek için onay (confirm=True) gereklidir.")
            
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"DELETE FROM {self._table}")
            self.conn.commit()
            logger.info("Tüm CV'ler silindi.")
        except sqlite3.Error as e:
            logger.error("CV'ler silinirken veritabanı hatası: %s", e)
            self.conn.rollback()
            raise
