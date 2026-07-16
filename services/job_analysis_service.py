import re
import logging
from typing import Dict, List
from utils.field_extractor import FieldExtractor
from utils.skill_dictionary import (
    TECH_SKILLS, SOFT_SKILLS, JOB_SECTION_PATTERNS,
    EXPERIENCE_KEYWORDS_EN, EXPERIENCE_KEYWORDS_TR,
    EDUCATION_KEYWORDS_EN, EDUCATION_KEYWORDS_TR,
)
from utils.language_detector import detect_language
from repositories.cv_repository import CVRepository
from models.cv_snapshot import CVSnapshot
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

logger = logging.getLogger(__name__)

# Pre-compile patterns used across methods
_SECTION_CLEAN_RE = re.compile(r'[^a-zçğıöşü\s]', re.IGNORECASE)

# Extended stopword list for keyword extraction
_STOPWORDS = frozenset({
    "this", "that", "with", "from", "have", "will", "your", "about",
    "they", "been", "their", "which", "would", "there", "could",
    "other", "more", "some", "than", "very", "when", "what", "were",
    "also", "each", "just", "like", "only", "over", "such", "take",
    "into", "then", "them", "these", "those", "most", "must", "able",
    "should", "shall", "being", "does", "done", "make", "made",
    "need", "well", "want", "good", "know", "look", "help", "first",
    "every", "back", "many", "much", "same", "still", "both", "keep",
    "olan", "için", "icin", "gibi", "daha", "veya", "bile", "evet",
    "olarak", "ilgili", "sahip", "kadar", "sonra", "olan", "yapı",
    "yapabilme", "birlikte", "arasında", "konusunda", "alanında",
    "olmak", "yapmak", "etmek", "bulunmak", "çalışmak", "almak",
    "vermek", "gelmek", "gitmek", "bilmek", "istemek", "bulmak",
})


class JobAnalysisService:
    def __init__(self):
        self._extractor = FieldExtractor()
        self._cv_repo = CVRepository()
        # Pre-build section keyword index for faster lookups
        self._section_keywords = {}
        for category, keywords in JOB_SECTION_PATTERNS.items():
            for kw in keywords:
                self._section_keywords[kw.lower()] = category

    def analyze(self, job_text: str, force_lang: str = None) -> Dict:
        if not job_text.strip():
            return {}

        lang = force_lang if force_lang else detect_language(job_text)

        translated_text = ""
        analysis_text = job_text
        if lang == 'en':
            if GoogleTranslator is not None:
                try:
                    translator = GoogleTranslator(source='en', target='tr')
                    chunks = self._split_text_safe(job_text, 4000)
                    translated_chunks = [translator.translate(chunk) for chunk in chunks]
                    translated_text = "".join(translated_chunks)
                    analysis_text = translated_text
                except Exception as e:
                    logger.warning("Çeviri hatası: %s", e)
                    translated_text = f"Çeviri hatası (İnternet bağlantınızı kontrol edin): {e}\n\nOrijinal Metin:\n{job_text}"
            else:
                translated_text = f"Çeviri yapılamadı ('deep-translator' kütüphanesi eksik). \nLütfen terminalden 'pip install deep-translator' komutunu çalıştırın.\n\nOrijinal Metin:\n{job_text}"
        else:
            translated_text = job_text

        lines = [l.strip() for l in analysis_text.strip().split('\n') if l.strip()]
        sections = self._split_into_sections(analysis_text)

        req_skills = self._extract_required_skills(analysis_text, sections, frozenset(TECH_SKILLS))
        soft_skills = self._extract_required_skills(analysis_text, sections, frozenset(SOFT_SKILLS))
        
        result = {
            "language": lang,
            "company_name": self._extract_company(analysis_text, lines, sections),
            "position": self._extract_position(analysis_text, lines, sections),
            "required_skills": req_skills,
            "soft_skills": soft_skills,
            "experience": self._extract_experience(analysis_text),
            "education": self._extract_education(analysis_text, lang),
            "location": self._extract_location(analysis_text),
            "work_type": self._extract_work_type(analysis_text),
            "salary": self._extract_salary(analysis_text),
            "responsibilities": self._extract_responsibilities(sections),
            "benefits": self._extract_benefits(sections),
            "keywords": self._extract_keywords(analysis_text),
            "full_translation": translated_text,
        }

        # CV Eşleşme Analizi
        latest_cv = self._cv_repo.get_latest()
        
        cv_match_score = 0
        matching_skills = []
        missing_skills = []
        cover_letter = ""
        suggestions = []
        
        if latest_cv and (req_skills or soft_skills):
            all_req_skills = req_skills + soft_skills
            cv_skills_lower = [s.lower() for s in latest_cv.skills]
            for skill in all_req_skills:
                if skill.lower() in cv_skills_lower:
                    matching_skills.append(skill)
                else:
                    missing_skills.append(skill)
            
            total_req = len(all_req_skills)
            if total_req > 0:
                cv_match_score = int((len(matching_skills) / total_req) * 100)
                
            # Ön Yazı Taslağı Oluştur
            company = result.get("company_name") or "[Şirket Adı]"
            pos = result.get("position") or "[Pozisyon]"
            
            if lang == "en":
                cover_letter = f"Dear Hiring Manager,\n\nI am writing to express my strong interest in the {pos} position at {company}. "
                if matching_skills:
                    skills_str = ", ".join(matching_skills[:3])
                    cover_letter += f"With my solid background and expertise in {skills_str}, I am confident in my ability to contribute effectively to your team.\n\n"
                else:
                    cover_letter += f"I am confident in my ability to contribute effectively to your team.\n\n"
                cover_letter += "I have attached my resume for your review. I look forward to the opportunity to discuss how my skills and experiences align with your needs.\n\nSincerely,\n" + (latest_cv.full_name or "[Adınız]")
            else:
                cover_letter = f"Sayın İlgili,\n\n{company} bünyesinde açılan {pos} pozisyonu ile yakından ilgileniyorum. "
                if matching_skills:
                    skills_str = ", ".join(matching_skills[:3])
                    cover_letter += f"Özellikle {skills_str} konularındaki tecrübelerim ve teknik yetkinliklerimle ekibinize değer katabileceğime inanıyorum.\n\n"
                else:
                    cover_letter += f"Sahip olduğum tecrübelerle ekibinize değer katabileceğime inanıyorum.\n\n"
                cover_letter += "Özgeçmişimi ekte bilginize sunuyorum. Niteliklerimin beklentilerinizle ne ölçüde uyuştuğunu detaylandırmak için görüşmeyi çok isterim.\n\nSaygılarımla,\n" + (latest_cv.full_name or "[Adınız]")
                
            if missing_skills:
                suggestions.append(f"Şu yetenekleri öğrenmek veya CV'nizde daha çok vurgulamak öne çıkmanızı sağlayabilir: {', '.join(missing_skills)}")
                
        result["cv_match_score"] = cv_match_score
        result["matching_skills"] = matching_skills
        result["missing_skills"] = missing_skills
        result["cover_letter"] = cover_letter
        result["suggestions"] = suggestions

        return result

    @staticmethod
    def _split_text_safe(text: str, max_len: int) -> List[str]:
        """Split text into chunks at word boundaries to avoid breaking words."""
        chunks = []
        while len(text) > max_len:
            split_at = text.rfind(' ', 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()
        if text:
            chunks.append(text)
        return chunks

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        lines = text.split('\n')
        sections = {}
        current_key = "header"
        current_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_lines:
                    current_lines.append("")
                continue

            stripped_lower = stripped.lower().rstrip(':').strip()
            stripped_clean = _SECTION_CLEAN_RE.sub('', stripped_lower).strip()

            matched = None
            for kw, cat in self._section_keywords.items():
                if stripped_clean == kw or stripped_lower == kw:
                    matched = cat
                    break
                if len(kw) > 5 and kw in stripped_clean:
                    matched = cat
                    break

            if not matched and len(stripped) < 60:
                is_likely_header = (
                    stripped.isupper() or
                    stripped.endswith(':') or
                    (stripped == stripped.title() and len(stripped.split()) <= 5)
                )
                if is_likely_header:
                    for kw, cat in self._section_keywords.items():
                        if kw in stripped_lower:
                            matched = cat
                            break

            if matched:
                if current_key and current_lines:
                    sections[current_key] = '\n'.join(current_lines).strip()
                current_key = matched
                current_lines = []
            else:
                # Heuristic for bullet points without headers
                if (stripped.startswith('•') or stripped.startswith('-')) and len(stripped) > 10:
                    stripped_lower_bp = stripped.lower()
                    if any(w in stripped_lower_bp for w in ["develop", "design", "maintain", "build", "collaborate", "geliştirmek", "yazmak", "tasarlamak"]):
                        if current_key != "responsibilities" and current_key not in ["requirements", "skills"]:
                            if current_key and current_lines:
                                sections[current_key] = '\n'.join(current_lines).strip()
                            current_key = "responsibilities"
                            current_lines = []
                    elif any(w in stripped_lower_bp for w in ["experience", "knowledge", "ability", "degree", "deneyim", "tecrübe", "bilgi", "hakim", "mezun"]):
                        if current_key != "requirements" and current_key not in ["responsibilities", "skills"]:
                            if current_key and current_lines:
                                sections[current_key] = '\n'.join(current_lines).strip()
                            current_key = "requirements"
                            current_lines = []
                            
                current_lines.append(line)

        if current_key and current_lines:
            sections[current_key] = '\n'.join(current_lines).strip()

        return sections

    def _extract_company(self, text: str, lines: List[str], sections: Dict) -> str:
        patterns = [
            re.compile(r'(?:company|firma|şirket|sirket|employer|şirket adı|sirket adi)\s*[:\-–]\s*(.+)', re.IGNORECASE),
            re.compile(r'^(.+?)\s+(?:is hiring|is looking|seeks|arıyor|ariyor|bünyesine|bunyesine)', re.IGNORECASE | re.MULTILINE),
            re.compile(r'\b(?:at|@)\s+([A-Z][a-zA-Z0-9&\-\s]{1,20})\s+(?:we|is|are|for)\b', re.MULTILINE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                result = m.group(1).strip().rstrip('.,;:')
                if len(result) < 80:
                    return result

        if "about" in sections:
            about = sections["about"]
            first_line = about.split('\n')[0].strip()
            if first_line and len(first_line) < 60:
                return first_line

        title_keywords = {
            "developer", "engineer", "specialist", "analyst", "manager",
            "designer", "intern", "mühendis", "uzman", "geliştirici",
            "stajyer", "pozisyon", "position", "role", "job",
        }
        if lines:
            for line in lines[:3]:
                lower = line.lower()
                if not any(kw in lower for kw in title_keywords):
                    if len(line) < 60 and not re.search(r'[@:/]', line):
                        clean = re.sub(r'[^a-zA-ZçÇğĞıİöÖşŞüÜ0-9\s&.]', '', line).strip()
                        if clean and len(clean.split()) <= 6:
                            return clean

        return ""

    def _extract_position(self, text: str, lines: List[str], sections: Dict) -> str:
        patterns = [
            re.compile(r'(?:position|role|title|pozisyon|görev|gorev|unvan|açık pozisyon|acik pozisyon)\s*[:\-–]\s*(.+)', re.IGNORECASE),
            re.compile(r'(?:we are looking for|looking for|seeking|aranan pozisyon|arıyoruz)\s+(?:a\s+|an\s+)?(.+?)[\.\\n]', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                result = m.group(1).strip().rstrip('.,;:')
                if len(result) < 100:
                    return result

        position_keywords = {
            "developer", "engineer", "specialist", "analyst", "manager",
            "designer", "architect", "consultant", "intern", "lead",
            "mühendis", "muhendis", "uzman", "geliştirici", "gelistirici",
            "analist", "mimar", "stajyer", "danışman", "danisman",
            "scientist", "administrator", "coordinator",
        }
        for line in lines[:10]:
            lower = line.lower()
            for kw in position_keywords:
                if kw in lower and len(line) < 80:
                    return line.strip()

        return ""

    def _extract_required_skills(self, text: str, sections: Dict, skill_set: frozenset) -> List[str]:
        skills_text = text
        if "skills" in sections:
            skills_text = sections["skills"] + "\n" + text
        if "requirements" in sections:
            skills_text = sections["requirements"] + "\n" + skills_text

        found = self._extractor.extract_skills(skills_text, skill_set)

        extra_patterns = [
            re.compile(r'(?:bilgi sahibi|experience with|proficiency in|knowledge of|familiar with)\s+(.+?)[\.\\n]', re.IGNORECASE),
        ]
        for p in extra_patterns:
            matches = p.findall(text)
            for match in matches:
                extra = self._extractor.extract_skills(match, skill_set)
                found.extend(extra)

        # Case-insensitive deduplication preserving order
        seen = set()
        unique = []
        for skill in found:
            key = skill.lower()
            if key not in seen:
                seen.add(key)
                unique.append(skill)
        return unique

    def _extract_experience(self, text: str) -> str:
        patterns = [
            re.compile(r'(?:en az|minimum|at least|min\.?)\s*(\d+)\+?\s*(?:yıl|yil|year|years|yr)', re.IGNORECASE),
            re.compile(r'(\d+)\+?\s*(?:yıl|yil|year|years|yr)\s*(?:deneyim|experience|tecrübe|tecrube)', re.IGNORECASE),
            re.compile(r'(\d+)\s*-\s*(\d+)\s*(?:yıl|yil|year|years)\s*(?:deneyim|experience|arası|arasi)?', re.IGNORECASE),
            re.compile(r'(\d+)\+?\s*(?:yıl|yil|year|years)', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                groups = m.groups()
                if len(groups) == 2:
                    return f"{groups[0]}-{groups[1]} yıl"
                return f"{groups[0]}+ yıl"

        level_patterns = [
            (re.compile(r'\b(?:senior|kıdemli|kidemli|sr\.?)\b', re.IGNORECASE), "Senior (5+ yıl)"),
            (re.compile(r'\b(?:mid[- ]?level|orta düzey|orta duzey)\b', re.IGNORECASE), "Mid-Level (3-5 yıl)"),
            (re.compile(r'\b(?:junior|jr\.?)\b', re.IGNORECASE), "Junior (0-2 yıl)"),
            (re.compile(r'\b(?:intern|stajyer|staj)\b', re.IGNORECASE), "Stajyer"),
            (re.compile(r'\b(?:lead|principal|baş|bas)\b', re.IGNORECASE), "Lead/Principal (7+ yıl)"),
        ]
        for p, label in level_patterns:
            if p.search(text):
                return label

        return ""

    def _extract_education(self, text: str, lang: str) -> str:
        patterns = [
            re.compile(r'(?:eğitim|egitim|education|degree|mezuniyet)\s*[:\-–]\s*(.+?)[\n]', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                return m.group(1).strip()

        degree_patterns = [
            (re.compile(r'\b(?:doktora|phd|doctorate)\b', re.IGNORECASE), "Doktora"),
            (re.compile(r'\b(?:yüksek lisans|yuksek lisans|master|msc|ms|ma|mba)\b', re.IGNORECASE), "Yüksek Lisans"),
            (re.compile(r'\b(?:lisans|bachelor|bsc|bs|ba|üniversite|universite|degree)\b', re.IGNORECASE), "Lisans"),
            (re.compile(r'\b(?:ön lisans|on lisans|associate)\b', re.IGNORECASE), "Ön Lisans"),
        ]
        found = []
        for p, label in degree_patterns:
            if p.search(text):
                found.append(label)

        dept_patterns = [
            re.compile(r'\b(?:bilgisayar|computer science|yazılım|yazilim|software|bilişim|bilisim)\b', re.IGNORECASE),
            re.compile(r'\b(?:mühendislik|muhendislik|engineering|matematik|mathematics)\b', re.IGNORECASE),
            re.compile(r'\b(?:istatistik|statistics|fizik|physics|elektrik|electrical)\b', re.IGNORECASE),
        ]
        depts = []
        for p in dept_patterns:
            m = p.search(text)
            if m:
                depts.append(m.group(0))

        result_parts = []
        if found:
            result_parts.append(found[0])
        if depts:
            result_parts.append(", ".join(depts[:2]))
        return " - ".join(result_parts) if result_parts else ""

    def _extract_location(self, text: str) -> str:
        patterns = [
            re.compile(r'(?:location|lokasyon|konum|yer|şehir|sehir|city)\s*[:\-–]\s*(.+?)[\n]', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                return m.group(1).strip()

        cities = {
            "istanbul": "İstanbul", "ankara": "Ankara", "izmir": "İzmir",
            "bursa": "Bursa", "antalya": "Antalya", "adana": "Adana",
            "konya": "Konya", "gaziantep": "Gaziantep", "kocaeli": "Kocaeli",
            "eskişehir": "Eskişehir", "eskisehir": "Eskişehir",
            "trabzon": "Trabzon", "samsun": "Samsun", "denizli": "Denizli",
            "mersin": "Mersin", "kayseri": "Kayseri", "diyarbakır": "Diyarbakır",
            "sakarya": "Sakarya", "tekirdağ": "Tekirdağ",
            "new york": "New York", "london": "London", "berlin": "Berlin",
            "amsterdam": "Amsterdam", "san francisco": "San Francisco",
            "munich": "Munich", "zurich": "Zurich", "dubai": "Dubai",
        }
        text_lower = text.lower()
        for key, display in cities.items():
            if key in text_lower:
                return display
        return ""

    def _extract_work_type(self, text: str) -> str:
        text_lower = text.lower()

        remote_patterns = re.compile(r'\b(?:fully?\s*remote|100%\s*remote|tamamen\s*uzaktan|uzaktan\s*çalışma|uzaktan\s*calisma)\b', re.IGNORECASE)
        hybrid_patterns = re.compile(r'\b(?:hybrid|hibrit|hibrid|yarı\s*uzaktan|yari\s*uzaktan)\b', re.IGNORECASE)
        onsite_patterns = re.compile(r'\b(?:on[- ]?site|ofis\s*içi|ofis\s*ici|ofiste|yerinde|office\s*based)\b', re.IGNORECASE)

        found = []
        if remote_patterns.search(text):
            found.append("Remote")
        if hybrid_patterns.search(text):
            found.append("Hybrid")
        if onsite_patterns.search(text):
            found.append("On-site")

        if found:
            return " / ".join(found)

        if "remote" in text_lower and not any(w in text_lower for w in ["not remote", "no remote", "non-remote"]):
            context_check = re.search(r'(?:remote|uzaktan).{0,30}(?:available|possible|option|imkan|mümkün|mumkun)', text_lower)
            if context_check:
                return "Remote (opsiyonel)"

        return ""

    def _extract_salary(self, text: str) -> str:
        patterns = [
            re.compile(r'(?:salary|maaş|maas|ücret|ucret|compensation)\s*[:\-–]\s*(.+?)[\n\.]', re.IGNORECASE),
            re.compile(r'(\d{2,3}k\s*(?:-|–|to)\s*\d{2,3}k\s*(?:USD|EUR|GBP)?)', re.IGNORECASE),
            re.compile(r'([$£€₺]\s*\d{1,3}(?:[.,]\d{3})*(?:\s*[-–]\s*[$£€₺]?\s*\d{1,3}(?:[.,]\d{3})*)?)', re.IGNORECASE),
            re.compile(r'(\d{1,3}(?:[.,]\d{3})*\s*(?:-|–|to)\s*\d{1,3}(?:[.,]\d{3})*\s*(?:TL|USD|\$|€|EUR|GBP))', re.IGNORECASE),
            re.compile(r'(\$\s*\d{1,3}(?:,\d{3})*(?:\s*[-–]\s*\$?\s*\d{1,3}(?:,\d{3})*)?)', re.IGNORECASE),
            re.compile(r'(\d{1,3}(?:\.\d{3})*\s*(?:-|–)\s*\d{1,3}(?:\.\d{3})*\s*TL)', re.IGNORECASE),
        ]
        for p in patterns:
            m = p.search(text)
            if m:
                return m.group(1).strip() if m.lastindex else m.group(0).strip()
        return ""

    def _extract_responsibilities(self, sections: Dict) -> List[str]:
        text = sections.get("responsibilities", "")
        if not text:
            return []
        return self._extractor.extract_list_items(text)

    def _extract_benefits(self, sections: Dict) -> List[str]:
        text = sections.get("benefits", "")
        if not text:
            return []
        return self._extractor.extract_list_items(text)

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-ZçÇğĞıİöÖşŞüÜ]{4,}\b', text.lower())
        filtered = [w for w in words if w not in _STOPWORDS]
        freq = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
        # Filter out single-occurrence words for more meaningful keywords
        sorted_words = sorted(
            ((w, c) for w, c in freq.items() if c >= 2),
            key=lambda x: x[1], reverse=True,
        )
        # If we don't have enough keywords with freq>=2, fall back to freq>=1
        if len(sorted_words) < 10:
            sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, c in sorted_words[:20]]
