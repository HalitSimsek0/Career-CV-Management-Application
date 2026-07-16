from dataclasses import dataclass, field
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class CVSnapshot:
    id: Optional[int] = None
    full_name: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    website_url: str = ""
    location: str = ""
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experiences: List[dict] = field(default_factory=list)
    education: List[dict] = field(default_factory=list)
    projects: List[dict] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    volunteer: List[dict] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    personal_info: List[str] = field(default_factory=list)
    raw_text: str = ""
    original_filename: str = ""
    file_path: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "website_url": self.website_url,
            "location": self.location,
            "summary": self.summary,
            "skills": json.dumps(self.skills, ensure_ascii=False),
            "experiences": json.dumps(self.experiences, ensure_ascii=False),
            "education": json.dumps(self.education, ensure_ascii=False),
            "projects": json.dumps(self.projects, ensure_ascii=False),
            "languages": json.dumps(self.languages, ensure_ascii=False),
            "certifications": json.dumps(self.certifications, ensure_ascii=False),
            "volunteer": json.dumps(self.volunteer, ensure_ascii=False),
            "references": json.dumps(self.references, ensure_ascii=False),
            "personal_info": json.dumps(self.personal_info, ensure_ascii=False),
            "raw_text": self.raw_text,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
        }

    @classmethod
    def from_row(cls, row) -> "CVSnapshot":
        def parse_json(val, field_name):
            if not val:
                return []
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("JSON parse hatası, alan: %s, veri: %s, hata: %s", field_name, val[:50], e)
                return []

        def get_safe(key, default=""):
            # Check if key exists in row (which can be a sqlite3.Row or dict)
            try:
                return row[key] if row[key] is not None else default
            except KeyError:
                return default

        return cls(
            id=get_safe("id", None),
            full_name=get_safe("full_name"),
            email=get_safe("email"),
            phone=get_safe("phone"),
            linkedin_url=get_safe("linkedin_url"),
            github_url=get_safe("github_url"),
            website_url=get_safe("website_url"),
            location=get_safe("location"),
            summary=get_safe("summary"),
            skills=parse_json(get_safe("skills"), "skills"),
            experiences=parse_json(get_safe("experiences"), "experiences"),
            education=parse_json(get_safe("education"), "education"),
            projects=parse_json(get_safe("projects"), "projects"),
            languages=parse_json(get_safe("languages"), "languages"),
            certifications=parse_json(get_safe("certifications"), "certifications"),
            volunteer=parse_json(get_safe("volunteer"), "volunteer"),
            references=parse_json(get_safe("references"), "references"),
            personal_info=parse_json(get_safe("personal_info"), "personal_info"),
            raw_text=get_safe("raw_text"),
            original_filename=get_safe("original_filename"),
            file_path=get_safe("file_path"),
            created_at=get_safe("created_at"),
            updated_at=get_safe("updated_at"),
        )
