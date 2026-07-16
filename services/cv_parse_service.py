import re
import json
import shutil
import logging
from pathlib import Path
import fitz
import docx
from models.cv_snapshot import CVSnapshot
from repositories.cv_repository import CVRepository
from utils.field_extractor import FieldExtractor
from utils.skill_dictionary import (
    TECH_SKILLS, SECTION_HEADERS_EN, SECTION_HEADERS_TR,
)
from utils.language_detector import detect_language
from config import CV_STORAGE_DIR

logger = logging.getLogger(__name__)

# Date patterns used to avoid false-positive header detection
_DATE_PATTERN = re.compile(
    r'\b(?:\d{4}[\s/\-–]\d{2,4}|\d{1,2}[\s/\-–]\d{4}|'
    r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|'
    r'ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)'
    r'[\s,]*\d{2,4})\b',
    re.IGNORECASE,
)
_HTML_TAG = re.compile(r'<[^>]+>')


class CVParseService:
    def __init__(self):
        self._repo = CVRepository()
        self._extractor = FieldExtractor()

    def parse_file(self, file_path: str) -> CVSnapshot:
        path = Path(file_path)
        ext = path.suffix.lower()
        if ext == '.pdf':
            raw_text = self._extract_pdf_text(file_path)
        elif ext in ('.docx', '.doc'):
            raw_text = self._extract_docx_text(file_path)
        else:
            raise ValueError(f"Desteklenmeyen dosya formatı: {ext}")

        stored_path = self._store_file(path)
        cv = self._analyze_text(raw_text)
        cv.original_filename = path.name
        cv.file_path = str(stored_path)
        cv.raw_text = raw_text

        self._repo.clear_all(confirm=True)
        cv.id = self._repo.save(cv)
        return cv

    def _extract_pdf_text(self, file_path: str) -> str:
        doc = None
        try:
            doc = fitz.open(file_path)
            lines = []
            for page in doc:
                blocks = page.get_text("dict", sort=True).get("blocks", [])
                for block in blocks:
                    if block.get("type", 1) == 0:
                        for line in block.get("lines", []):
                            line_html = ""
                            for span in line.get("spans", []):
                                text = span.get("text", "")
                                if not text.strip():
                                    line_html += text
                                    continue

                                flags = span.get("flags", 0)
                                font = span.get("font", "").lower()
                                size = round(span.get("size", 12))

                                is_bold = (flags & 2**4) or "bold" in font
                                is_italic = (flags & 2**1) or "italic" in font

                                span_html = text.replace("<", "&lt;").replace(">", "&gt;")
                                if is_bold:
                                    span_html = f"<b>{span_html}</b>"
                                if is_italic:
                                    span_html = f"<i>{span_html}</i>"

                                span_html = f'<span style="font-size:{size}px;">{span_html}</span>'
                                line_html += span_html
                            if line_html.strip():
                                lines.append(line_html)
            return '\n'.join(lines)
        except Exception:
            logger.exception("PDF metin çıkarma hatası: %s", file_path)
            raise
        finally:
            if doc is not None:
                doc.close()

    def _extract_docx_text(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        parts = []
        for p in doc.paragraphs:
            if not p.text.strip():
                continue
            # Preserve bold/italic styling from runs
            line_html = ""
            for run in p.runs:
                text = run.text
                if not text:
                    continue
                span_html = text.replace("<", "&lt;").replace(">", "&gt;")
                if run.bold:
                    span_html = f"<b>{span_html}</b>"
                if run.italic:
                    span_html = f"<i>{span_html}</i>"
                line_html += span_html
            if line_html.strip():
                parts.append(line_html)
            elif p.text.strip():
                parts.append(p.text.strip())
        return '\n'.join(parts)

    def _store_file(self, source: Path) -> Path:
        dest = CV_STORAGE_DIR / source.name
        counter = 1
        while dest.exists():
            dest = CV_STORAGE_DIR / f"{source.stem}_{counter}{source.suffix}"
            counter += 1
        shutil.copy2(str(source), str(dest))
        return dest

    def _analyze_text(self, raw_text: str) -> CVSnapshot:
        plain_text = _HTML_TAG.sub('', raw_text)

        section_map = {**SECTION_HEADERS_EN, **SECTION_HEADERS_TR}
        sections_html = self._extractor.extract_sections(raw_text, section_map)
        sections_plain = self._extractor.extract_sections(plain_text, section_map)

        cv = CVSnapshot()
        cv.full_name = self._extractor.extract_name(plain_text)
        cv.email = self._extractor.extract_email(plain_text)
        cv.phone = self._extractor.extract_phone(plain_text)
        cv.linkedin_url = self._extractor.extract_linkedin(plain_text)
        cv.github_url = self._extractor.extract_github(plain_text)
        cv.website_url = self._extractor.extract_website(plain_text)
        cv.location = self._extractor.extract_location(plain_text)

        skills_from_text = self._extractor.extract_skills(plain_text, TECH_SKILLS)
        skills_from_section = []
        if "skills" in sections_plain:
            skill_lines = self._extractor.extract_list_items(sections_plain["skills"])
            for line in skill_lines:
                found = self._extractor.extract_skills(line, TECH_SKILLS)
                skills_from_section.extend(found)
                cleaned = line.strip()
                if cleaned and cleaned.lower() not in [s.lower() for s in skills_from_section]:
                    parts = [p.strip() for p in cleaned.replace(',', '|').replace('/', '|').split('|')]
                    for part in parts:
                        if part and len(part) > 1:
                            skills_from_section.append(part)
        all_skills = list(dict.fromkeys(skills_from_text + skills_from_section))
        cv.skills = all_skills

        cv.summary = sections_html.get("summary", "")

        if "experience" in sections_html:
            cv.experiences = self._parse_structured_section(sections_html["experience"])
        if "education" in sections_html:
            cv.education = self._parse_structured_section(sections_html["education"])
        if "projects" in sections_html:
            cv.projects = self._parse_structured_section(sections_html["projects"])
        if "languages" in sections_html:
            cv.languages = self._extractor.extract_list_items(sections_html["languages"])
        if "certifications" in sections_html:
            cv.certifications = self._extractor.extract_list_items(sections_html["certifications"])
        if "volunteer" in sections_html:
            cv.volunteer = self._parse_structured_section(sections_html["volunteer"])
        if "references" in sections_html:
            cv.references = self._extractor.extract_list_items(sections_html["references"])
        if "personal_info" in sections_html:
            cv.personal_info = self._extractor.extract_list_items(sections_html["personal_info"])

        # Append extra sections (interests, awards) to summary so they are not lost
        extra = {}
        if "interests" in sections_html:
            extra["interests"] = self._extractor.extract_list_items(sections_html["interests"])
        if "awards" in sections_html:
            extra["awards"] = self._extractor.extract_list_items(sections_html["awards"])

        if extra:
            existing = cv.summary or ""
            if existing:
                existing += "\n\n"
            for key, val in extra.items():
                section_names = {
                    "references": "Referanslar",
                    "volunteer": "Gönüllü Çalışmalar",
                    "interests": "İlgi Alanları",
                    "awards": "Ödüller",
                }
                name = section_names.get(key, key)
                if isinstance(val, list) and val:
                    if isinstance(val[0], dict):
                        items_text = []
                        for item in val:
                            title = item.get("title", "")
                            details = item.get("details", [])
                            items_text.append(f"{title}: {', '.join(details)}" if details else title)
                        existing += f"[{name}]\n" + "\n".join(items_text) + "\n\n"
                    else:
                        existing += f"[{name}]\n" + "\n".join(str(v) for v in val) + "\n\n"
            # FIX: Actually assign the built string back to cv.summary
            cv.summary = existing

        return cv

    def _parse_structured_section(self, text: str) -> list:
        entries = []
        current = None
        lines = text.split('\n')

        for line in lines:
            line_plain = _HTML_TAG.sub('', line)
            stripped = line_plain.strip()

            if not stripped:
                if current:
                    entries.append(current)
                    current = None
                continue

            is_bullet = stripped.startswith(('•', '-', '▪', '▸', '►', '*'))

            # Improved header detection: skip lines that are primarily dates
            has_date = bool(_DATE_PATTERN.search(stripped))

            is_header = (
                not is_bullet and
                not has_date and
                len(stripped) < 120 and
                (
                    stripped.isupper() or
                    (stripped[0].isupper() and not stripped.endswith('.')) or
                    any(c.isdigit() for c in stripped[:4])
                )
            )

            if current is None:
                current = {"title": line, "details": []}
            elif is_header and len(current.get("details", [])) > 0:
                entries.append(current)
                current = {"title": line, "details": []}
            else:
                detail = line
                if detail.strip():
                    if not is_header and not is_bullet and not current["details"]:
                        pass
                    current["details"].append(detail)

        if current:
            entries.append(current)

        return entries

    def get_latest_cv(self):
        return self._repo.get_latest()

    def get_all_cvs(self):
        return self._repo.get_all()

    def update_cv(self, cv: CVSnapshot):
        return self._repo.update(cv)

    def delete_cv(self, cv_id: int):
        self._repo.clear_all(confirm=True)
        return True
