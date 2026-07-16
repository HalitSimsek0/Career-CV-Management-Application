import logging
from typing import List
import sqlite3
from repositories.base_repository import BaseRepository
from models.planned_company import PlannedCompany

logger = logging.getLogger(__name__)


class PlannedCompanyRepository(BaseRepository):
    def __init__(self):
        super().__init__("planned_companies")

    def save(self, company: PlannedCompany) -> int:
        data = company.to_dict()
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
            logger.error("Planlanan şirket kaydedilirken DB hatası: %s", e)
            self.conn.rollback()
            raise

    def get_all(self, limit: int = None, offset: int = None) -> List[PlannedCompany]:
        rows = self.find_all(limit=limit, offset=offset)
        return [PlannedCompany.from_row(r) for r in rows]

    def update(self, company: PlannedCompany):
        is_applied_val = 1 if company.is_applied is True else (0 if company.is_applied is False else None)
        cursor = self.conn.cursor()
        cursor.execute(
            f"UPDATE {self._table} SET company_name = ?, is_applied = ? WHERE id = ?",
            (company.company_name, is_applied_val, company.id)
        )
        self.conn.commit()

    def search(self, query: str) -> List[PlannedCompany]:
        all_companies = self.get_all()
        from utils.string_utils import search_normalize
        
        q = search_normalize(query)
        filtered = []
        for c in all_companies:
            if q in search_normalize(c.company_name):
                filtered.append(c)
        return filtered

    def exists_by_name(self, company_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            f"SELECT 1 FROM {self._table} WHERE LOWER(company_name) = LOWER(?)",
            (company_name,),
        )
        return cursor.fetchone() is not None
