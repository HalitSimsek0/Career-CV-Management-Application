import re
from typing import List, Dict
from functools import lru_cache

TITLE_KEYWORDS = frozenset({
    "developer", "engineer", "designer", "manager", "analyst", "architect",
    "consultant", "specialist", "intern", "lead", "senior", "junior",
    "full stack", "fullstack", "frontend", "backend", "devops", "qa",
    "data scientist", "data engineer", "data analyst", "product",
    "software", "web", "mobile", "cloud", "system", "network",
    "mühendis", "muhendis", "geliştirici", "gelistirici", "uzman",
    "stajyer", "yönetici", "yonetici", "analist", "mimar", "danışman",
    "danisman", "tasarımcı", "tasarimci", "programcı", "programci",
})


class FieldExtractor:
    EMAIL_PATTERN = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}'
    )
    LINKEDIN_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?', re.IGNORECASE
    )
    GITHUB_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?github\.com/[\w-]+/?', re.IGNORECASE
    )
    GITHUB_PATTERN_LOOSE = re.compile(
        r'github\s*[.:]\s*(?:https?://)?(?:www\.)?github\.?\s*c\s*o\s*m\s*/\s*([\w-]+)',
        re.IGNORECASE
    )
    WEBSITE_PATTERN = re.compile(
        r'https?://(?!.*(?:linkedin|github))[\w.-]+\.\w{2,}(?:/\S*)?', re.IGNORECASE
    )
    EXPERIENCE_YEAR_PATTERN = re.compile(
        r'(\d+)\+?\s*(?:yıl|yil|year|years|yr|yrs)', re.IGNORECASE
    )

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_sorted_skills(skill_set: frozenset) -> List[str]:
        # Cache sorted skills to avoid re-sorting on every extract_skills call
        return sorted(skill_set, key=len, reverse=True)

    def extract_email(self, text: str) -> str:
        match = self.EMAIL_PATTERN.search(text)
        return match.group(0) if match else ""

    def extract_phone(self, text: str) -> str:
        match = self.PHONE_PATTERN.search(text)
        return match.group(0).strip() if match else ""

    def extract_linkedin(self, text: str) -> str:
        match = self.LINKEDIN_PATTERN.search(text)
        if match:
            return match.group(0)
        loose = re.search(
            r'linkedin\s*[.:]\s*((?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+)',
            text, re.IGNORECASE
        )
        if loose:
            return loose.group(1)
        loose2 = re.search(
            r'linkedin\s*[.:]\s*(www\.linkedin\.com/in/[\w-]+)',
            text, re.IGNORECASE
        )
        if loose2:
            return loose2.group(1)
        return ""

    def extract_github(self, text: str) -> str:
        match = self.GITHUB_PATTERN.search(text)
        if match:
            return match.group(0)
        loose = self.GITHUB_PATTERN_LOOSE.search(text)
        if loose:
            username = loose.group(1).strip()
            return f"github.com/{username}"
        normalized = re.sub(r'\s+', '', text)
        match2 = re.search(r'github\.com/([\w-]+)', normalized, re.IGNORECASE)
        if match2:
            return f"github.com/{match2.group(1)}"
        return ""

    def extract_website(self, text: str) -> str:
        match = self.WEBSITE_PATTERN.search(text)
        return match.group(0) if match else ""

    def _is_title_line(self, line: str) -> bool:
        lower = line.lower().strip()
        lower_clean = re.sub(r'[&|/,]', ' ', lower)
        for kw in TITLE_KEYWORDS:
            if kw in lower_clean:
                return True
        if re.search(r'\b(?:developer|engineer|designer|manager|analyst)\b', lower, re.IGNORECASE):
            return True
        return False

    def extract_name(self, text: str) -> str:
        lines = text.strip().split('\n')
        # Check top 8 lines
        for line in lines[:8]:
            line = line.strip()
            if not line:
                continue
            if self.EMAIL_PATTERN.search(line) or self.PHONE_PATTERN.search(line):
                continue
            if self.LINKEDIN_PATTERN.search(line) or 'linkedin' in line.lower():
                continue
            if 'github' in line.lower() or self._is_title_line(line):
                continue
            if '@' in line or re.search(r'https?://', line):
                continue
                
            cleaned = re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜâÂ\s]', '', line).strip()
            words = cleaned.split()
            # Relaxed constraint: Allow single word (mononym) up to 5 words
            if 1 <= len(words) <= 5 and all(len(w) >= 2 for w in words):
                has_upper = any(c.isupper() for c in cleaned)
                if has_upper or cleaned == cleaned.title():
                    return cleaned
                    
        # Fallback to top 5 lines if strict check fails
        for line in lines[:5]:
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜâÂ\s]', '', line).strip()
            words = cleaned.split()
            if 1 <= len(words) <= 4:
                return cleaned
        return ""

    def extract_skills(self, text: str, skill_set: set) -> List[str]:
        text_lower = text.lower()
        text_normalized = re.sub(r'[^a-z0-9çğıöşü#+.\s/]', ' ', text_lower)
        found = []
        
        # Optimize by caching the sorted set if passed as frozenset
        # Or sort normally if standard set
        if isinstance(skill_set, frozenset):
            sorted_skills = self._get_sorted_skills(skill_set)
        else:
            sorted_skills = sorted(skill_set, key=len, reverse=True)
            
        for skill in sorted_skills:
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill) + r'(?![a-zA-Z0-9])'
            if re.search(pattern, text_normalized):
                found.append(skill)
        return found

    def extract_experience_years(self, text: str) -> str:
        patterns = [
            re.compile(r'(\d+)\+?\s*(?:yıl|yil|year|years|yr|yrs)', re.IGNORECASE),
            re.compile(r'(?:en az|minimum|at least)\s*(\d+)\s*(?:yıl|yil|year|years)', re.IGNORECASE),
            re.compile(r'(\d+)\s*-\s*(\d+)\s*(?:yıl|yil|year|years)', re.IGNORECASE),
        ]
        for p in patterns:
            matches = p.findall(text)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]}-{matches[0][1]} yıl"
                return f"{max(int(m) for m in matches)} yıl"
        return ""

    def extract_sections(self, text: str, section_map: dict) -> Dict[str, str]:
        lines = text.split('\n')
        sections = {}
        current_section = None
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_section:
                    current_lines.append("")
                continue
                
            plain_line = re.sub(r'<[^>]+>', '', stripped)
            stripped_lower = plain_line.lower()
            stripped_clean = re.sub(r'[^a-zçğıöşüa-z\s]', '', stripped_lower).strip()

            matched = None
            for key in section_map:
                if stripped_clean == key or stripped_lower == key:
                    matched = section_map[key]
                    break
            if not matched:
                for key in section_map:
                    if stripped_clean.startswith(key) and len(stripped_clean) - len(key) < 5:
                        matched = section_map[key]
                        break
            if not matched and len(plain_line) < 40:
                is_header = (
                    plain_line.isupper() or
                    (plain_line == plain_line.title() and len(plain_line.split()) <= 4) or
                    plain_line.endswith(':')
                )
                if is_header:
                    check = re.sub(r'[:\s]', '', stripped_lower)
                    check_clean = re.sub(r'[^a-zçğıöşü\s]', '', check).strip()
                    for key in section_map:
                        key_clean = re.sub(r'[^a-zçğıöşü\s]', '', key).strip()
                        if check_clean == key_clean:
                            matched = section_map[key]
                            break

            if matched:
                if current_section and current_lines:
                    # Append instead of overwrite if section is duplicated (e.g. split across pages)
                    if current_section in sections:
                        sections[current_section] += '\n' + '\n'.join(current_lines).strip()
                    else:
                        sections[current_section] = '\n'.join(current_lines).strip()
                current_section = matched
                current_lines = []
            elif current_section:
                current_lines.append(line)

        if current_section and current_lines:
            if current_section in sections:
                sections[current_section] += '\n' + '\n'.join(current_lines).strip()
            else:
                sections[current_section] = '\n'.join(current_lines).strip()

        return sections

    def extract_list_items(self, text: str) -> List[str]:
        items = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            line = re.sub(r'^[\-•●○▪▸►→·\*]\s*', '', line)
            line = re.sub(r'^\d+[.)]\s*', '', line)
            if line and len(line) > 1:
                items.append(line)
        return items

    def extract_location(self, text: str) -> str:
        patterns = [
            re.compile(r'(?:location|lokasyon|konum|adres|address)\s*[:\-–]\s*(.+)', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                return m.group(1).strip()
        cities = frozenset([
            "istanbul", "ankara", "izmir", "bursa", "antalya", "adana",
            "konya", "gaziantep", "kocaeli", "eskişehir", "trabzon",
            "samsun", "denizli", "mersin", "kayseri", "diyarbakır",
            "new york", "london", "berlin", "paris", "amsterdam",
            "san francisco", "remote", "uzaktan",
        ])
        text_lower = text.lower()
        for city in cities:
            if city in text_lower:
                return city.capitalize()
        return ""
