from typing import List, Optional
from database.connection import DatabaseConnection


class BaseRepository:
    _ALLOWED_TABLES = frozenset({"cv_snapshots", "job_applications", "planned_companies", "migrations"})

    def __init__(self, table_name: str):
        if table_name not in self._ALLOWED_TABLES:
            raise ValueError(f"Geçersiz tablo adı: {table_name}")
        self._table = table_name
        self._db = DatabaseConnection()

    @property
    def conn(self):
        return self._db.get_connection()

    def find_by_id(self, record_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {self._table} WHERE id = ?", (record_id,))
        return cursor.fetchone()

    def exists(self, record_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT 1 FROM {self._table} WHERE id = ?", (record_id,))
        return cursor.fetchone() is not None

    def find_all(self, limit: int = None, offset: int = None) -> List[dict]:
        query = f"SELECT * FROM {self._table} ORDER BY id DESC"
        params = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def delete(self, record_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self._table} WHERE id = ?", (record_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) as cnt FROM {self._table}")
        return cursor.fetchone()["cnt"]
