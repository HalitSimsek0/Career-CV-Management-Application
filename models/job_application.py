from dataclasses import dataclass
from typing import Optional


@dataclass
class JobApplication:
    id: Optional[int] = None
    company_name: str = ""
    position: str = ""
    status: str = "applied"
    application_date: str = ""
    response_date: str = ""
    source: str = ""
    salary_range: str = ""
    contact_person: str = ""
    contact_email: str = ""
    job_url: str = ""
    notes: str = ""  # New field for taking custom notes on applications
    created_at: str = ""
    updated_at: str = ""

    VALID_STATUSES = frozenset([
        "applied",
        "interview",
        "rejected",
        "accepted",
    ])

    def __post_init__(self):
        # Validate status immediately on instantiation
        if self.status not in self.VALID_STATUSES:
            self.status = "applied"

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "position": self.position,
            "status": self.status,
            "application_date": self.application_date,
            "response_date": self.response_date,
            "source": self.source,
            "salary_range": self.salary_range,
            "contact_person": self.contact_person,
            "contact_email": self.contact_email,
            "job_url": self.job_url,
            "notes": self.notes,
        }

    @classmethod
    def from_row(cls, row) -> "JobApplication":
        def get_safe(key, default=""):
            try:
                return row[key] if row[key] is not None else default
            except KeyError:
                return default

        return cls(
            id=get_safe("id", None),
            company_name=get_safe("company_name"),
            position=get_safe("position"),
            status=get_safe("status", "applied"),
            application_date=get_safe("application_date"),
            response_date=get_safe("response_date"),
            source=get_safe("source"),
            salary_range=get_safe("salary_range"),
            contact_person=get_safe("contact_person"),
            contact_email=get_safe("contact_email"),
            job_url=get_safe("job_url"),
            notes=get_safe("notes"),
            created_at=get_safe("created_at"),
            updated_at=get_safe("updated_at"),
        )

    @property
    def status_display(self) -> str:
        status_map = {
            "applied": "Başvuruldu",
            "interview": "Mülakat",
            "rejected": "Reddedildi",
            "accepted": "Kabul Edildi",
        }
        return status_map.get(self.status, self.status)
