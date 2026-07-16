import logging
from typing import Optional, List
import sqlite3
from repositories.base_repository import BaseRepository
from models.job_application import JobApplication

logger = logging.getLogger(__name__)


class ApplicationRepository(BaseRepository):
    def __init__(self):
        super().__init__("job_applications")

    def save(self, app: JobApplication) -> int:
        data = app.to_dict()
        columns = ", ".join(data.keys())
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
            logger.error("Başvuru kaydedilirken DB hatası: %s", e)
            self.conn.rollback()
            raise

    def update(self, app: JobApplication) -> bool:
        if app.id is None:
            return False
            
        data = app.to_dict()
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"UPDATE {self._table} SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
                list(data.values()) + [app.id],
            )
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error("Başvuru güncellenirken DB hatası (id=%s): %s", app.id, e)
            self.conn.rollback()
            raise

    def get_by_id(self, app_id: int) -> Optional[JobApplication]:
        row = self.find_by_id(app_id)
        if row:
            return JobApplication.from_row(row)
        return None

    def get_all(self, limit: int = None, offset: int = None) -> List[JobApplication]:
        rows = self.find_all(limit=limit, offset=offset)
        return [JobApplication.from_row(r) for r in rows]

    def search(self, query: str, limit: int = None, offset: int = None) -> List[JobApplication]:
        all_apps = self.get_all()
        
        from utils.string_utils import search_normalize
            
        q = search_normalize(query)
        filtered = []
        for app in all_apps:
            if q in search_normalize(app.company_name) or q in search_normalize(app.position):
                filtered.append(app)
                
        if offset is not None:
            filtered = filtered[offset:]
        if limit is not None:
            filtered = filtered[:limit]
            
        return filtered

    def filter_by_status(self, status: str, limit: int = None, offset: int = None) -> List[JobApplication]:
        cursor = self.conn.cursor()
        sql = f"SELECT * FROM {self._table} WHERE status = ? ORDER BY created_at DESC"
        params = [status]
        
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                sql += " OFFSET ?"
                params.append(offset)
                
        cursor.execute(sql, tuple(params))
        return [JobApplication.from_row(r) for r in cursor.fetchall()]

    def get_by_company(self, company_name: str) -> List[JobApplication]:
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT * FROM {self._table} WHERE LOWER(company_name) = LOWER(?) ORDER BY created_at DESC",
            (company_name,),
        )
        return [JobApplication.from_row(r) for r in cursor.fetchall()]

    def get_stats(self) -> dict:
        cursor = self.conn.cursor()
        
        # Optimize count and status grouping in single execution block if possible,
        # but SQLite is fast enough for separate quick queries.
        cursor.execute(f"SELECT COUNT(*) as total FROM {self._table}")
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"SELECT status, COUNT(*) as cnt FROM {self._table} GROUP BY status"
        )
        by_status = {row["status"]: row["cnt"] for row in cursor.fetchall()}

        cursor.execute(
            f"SELECT COUNT(DISTINCT LOWER(company_name)) as unique_companies FROM {self._table}"
        )
        unique_companies = cursor.fetchone()["unique_companies"]

        cursor.execute(
            f"""SELECT company_name, COUNT(*) as cnt
            FROM {self._table} GROUP BY LOWER(company_name) ORDER BY cnt DESC"""
        )
        top_companies = [(row["company_name"], row["cnt"]) for row in cursor.fetchall()]

        cursor.execute(
            f"""SELECT strftime('%Y-%m', application_date) as month, COUNT(*) as cnt
            FROM {self._table} WHERE application_date != '' AND application_date IS NOT NULL
            GROUP BY month ORDER BY month DESC LIMIT 12"""
        )
        monthly = [(row["month"], row["cnt"]) for row in cursor.fetchall()]

        cursor.execute(
            f"""SELECT application_date as day, COUNT(*) as cnt
            FROM {self._table} WHERE application_date != '' AND application_date IS NOT NULL
            GROUP BY day ORDER BY day DESC"""
        )
        daily = [(row["day"], row["cnt"]) for row in cursor.fetchall()]

        return {
            "total": total,
            "by_status": by_status,
            "unique_companies": unique_companies,
            "top_companies": top_companies,
            "monthly": monthly,
            "daily": daily,
        }
