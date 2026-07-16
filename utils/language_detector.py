import re

# Use frozenset for O(1) immutable lookups and performance
_EN_WORDS = frozenset({
    "the", "and", "to", "of", "a", "in", "is", "that", "for", "on", 
    "with", "as", "at", "by", "an", "be", "this", "are", "from",
    "we", "our", "your", "requirements", "experience", "skills",
    "who", "have", "development", "developer", "knowledge", "design",
    "team", "work", "working", "using", "with", "system", "systems"
})

_TR_WORDS = frozenset({
    "ve", "ile", "bir", "bu", "için", "icin", "olan", "veya", 
    "gibi", "daha", "çok", "cok", "den", "dan", "olarak",
    "aranan", "gerekli", "sahip", "istenen", "nitelikler",
    "adaylar", "arıyoruz", "ariyoruz", "deneyimli", "bilgisi",
    "çalışma", "calisma", "sistemleri", "takım", "takim", "iş", "is"
})

_TR_CHARS = frozenset("çÇğĞıİöÖşŞüÜ")


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "en"  # Default fallback
        
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    total_words = len(words)
    if total_words == 0:
        return "en"
        
    en_count = sum(1 for w in words if w in _EN_WORDS)
    tr_count = sum(1 for w in words if w in _TR_WORDS)
    
    # Normalize scores by total words to handle short vs long texts fairly
    en_ratio = en_count / total_words
    tr_ratio = tr_count / total_words
    
    if en_ratio > tr_ratio:
        return "en"
    elif tr_ratio > en_ratio:
        return "tr"
        
    # Fallback to Turkish character counting if ratios are equal (or zero)
    tr_char_count = sum(1 for c in text if c in _TR_CHARS)
    if tr_char_count > 5:
        return "tr"
        
    return "en"
