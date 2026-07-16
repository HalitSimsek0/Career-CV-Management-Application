from dataclasses import dataclass
from typing import Optional


@dataclass
class PlannedCompany:
    id: Optional[int] = None
    company_name: str = ""
    created_at: str = ""
    is_applied: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "is_applied": 1 if self.is_applied is True else (0 if self.is_applied is False else None)
        }

    @classmethod
    def from_row(cls, row) -> "PlannedCompany":
        def get_safe(key, default=""):
            try:
                return row[key] if row[key] is not None else default
            except KeyError:
                return default

        try:
            is_applied_val = row["is_applied"]
        except KeyError:
            is_applied_val = None

        is_applied = None
        if is_applied_val == 1:
            is_applied = True
        elif is_applied_val == 0:
            is_applied = False

        return cls(
            id=get_safe("id", None),
            company_name=get_safe("company_name"),
            created_at=get_safe("created_at"),
            is_applied=is_applied,
        )
