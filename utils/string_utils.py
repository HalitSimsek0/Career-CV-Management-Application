def turkish_upper(text: str) -> str:
    """Converts a string to uppercase according to Turkish rules."""
    if not text:
        return text
    text = text.replace("i", "İ").replace("ı", "I")
    return text.upper()

def turkish_lower(text: str) -> str:
    """Converts a string to lowercase according to Turkish rules."""
    if not text:
        return text
    text = text.replace("İ", "i").replace("I", "ı")
    return text.lower()

def search_normalize(text: str) -> str:
    """Normalizes a string for search purposes, mapping Turkish characters to ASCII."""
    if not text:
        return text
    text = text.replace("İ", "i").replace("I", "i").replace("ı", "i")
    text = text.replace("Ü", "u").replace("ü", "u").replace("Ö", "o").replace("ö", "o")
    text = text.replace("Ş", "s").replace("ş", "s").replace("Ç", "c").replace("ç", "c")
    text = text.replace("Ğ", "g").replace("ğ", "g")
    return text.lower()
