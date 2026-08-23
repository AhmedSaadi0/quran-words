import re

DIACRITICS_RE = re.compile(
    r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]"
)


def strip_diacritics(s: str) -> str:
    if not s:
        return ""
    return DIACRITICS_RE.sub("", s)


def normalize_ar(s: str) -> str:
    """Normalize Arabic text for search: strip diacritics + unify alef/yeh forms."""
    if not s:
        return ""
    s = strip_diacritics(s)
    s = (
        s.replace("ٱ", "ا")
        .replace("ـ", "")
        .replace("آ", "ا")
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("ى", "ي")
    )
    return s.strip()


def normalize_query(q: str) -> str:
    return normalize_ar(q)
