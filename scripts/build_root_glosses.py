#!/usr/bin/env python3
"""
بناء المعنى السريع الشامل لكل جذر (gloss) — سطر أو سطران مختصران
Stage: Build short root glosses table.

الفكرة: جداول root_meanings نصوص طويلة جداً (متوسط 4,400 حرف من 8 قواميس).
نستخرج من كل قاموس أول عبارة تعريفية قصيرة (سطر/سطرين) لبناء:
  - gloss_ar : المعنى العربي المختصر (يفضل الراغب لمنحه القرآني)
  - gloss_en : الترجمة الإنجليزية المختصرة (من معجم لين)

ترتيب القواميس العربية (fallback تلقائي عند فشل الاستخراج):
  1) المفردات في غريب القرآن للراغب الأصفهاني
  2) المحكم والمحيط الأعظم لابن سيده الأندلسي
  3) تاج اللغة وصِحاح العربية للجوهري
  4) أساس البلاغة للزمخشري
  5) كتاب العين للخليل بن أحمد الفراهيدي
  6) لسان العرب لابن منظور
  7) تاج العروس لمرتضى الزبيدي

أنماط الاستخراج:
  أ) نمط «الحاشية: التعريف» — نأخذ ما بعد أول ":" حتى أول فاصل (، . ؛)
  ب) نمط «[جذر] الكذِب.» — نزل الأقواس ثم أول جملة حتى "."، ونشيل تكرار حروف الجذر

الاستعمال:
  python scripts/build_root_glosses.py            # بناء + تقرير
  python scripts/build_root_glosses.py --samples  # عرض عينات للمراجعة

الخرج: جدول جديد في data/quran_words.db (إضافة آمنة فقط):
  root_glosses(root_id PK, gloss_ar, gloss_en, ar_source, en_source)
"""

import argparse
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"

AR_BOOKS = [
    "المفردات في غريب القرآن للراغب الأصفهاني",
    "المحكم والمحيط الأعظم لابن سيده الأندلسي",
    "تاج اللغة وصِحاح العربية للجوهري",
    "أساس البلاغة للزمخشري",
    "كتاب العين للخليل بن أحمد الفراهيدي",
    "لسان العرب لابن منظور",
    "تاج العروس لمرتضى الزبيدي",
]

EN_BOOK_LIKE = "%إنجليزي%"

MAX_AR = 120
MIN_AR = 8
MAX_EN = 110

DIACRITICS_RE = re.compile(
    r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]"
)

# فواصل نهاية العبارة التعريفية الأولى
CUT_CHARS = "،;.؛:—–"


def strip_diacritics(s: str) -> str:
    return DIACRITICS_RE.sub("", s)


def clean_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def cap_at_word(s: str, limit: int) -> str:
    """قص عند حد كلمة قبل الحد الأقصى."""
    if len(s) <= limit:
        return s
    cut = s[:limit]
    sp = cut.rfind(" ")
    return cut[:sp] if sp > limit * 0.5 else cut


def first_clause(text: str) -> str | None:
    """أول عبارة قبل أي فاصلة/نقطة. يرجع None إن كانت قصيرة جداً."""
    text = clean_ws(text)
    if not text:
        return None
    out = []
    for ch in text:
        if ch in CUT_CHARS:
            break
        out.append(ch)
    clause = "".join(out).strip(" ،؛.")
    if len(strip_diacritics(clause)) >= MIN_AR:
        return clause
    # العبارة الأولى قصيرة (مثل «الكذِب») — مدّدها للفاصلة الثانية
    parts = re.split(r"[،;]", text, maxsplit=2)
    extended = parts[0] if len(parts) == 1 else "، ".join(parts[:2])
    extended = extended.strip(" ،؛.")
    if len(strip_diacritics(extended)) >= MIN_AR:
        return cap_at_word(extended, MAX_AR)
    return clause or None


def extract_arabic(definition: str, root: str) -> tuple[str | None, str]:
    """
    يرجع (gloss, method) — method: colon|sentence|extended|none
    """

    def is_bad(clause: str) -> bool:
        """آيات وشواهد بدل تعريف — نرفضها وننتقل للقاموس التالي."""
        if re.search(r"\[[^\]]{0,30}/", clause):  # مرجع آية مثل [البقرة/ 255]
            return True
        if "«" in clause or "»" in clause or "{" in clause or "}" in clause:
            return True
        if '"' in clause or "*" in clause:
            return True
        if clause.startswith(("قوله تعالى", "قال", "وقيل")) or "قال الله" in clause:
            return True
        # «قال تعالى/الله/النبي…» في أي موضع — شاهد لا تعريف
        if re.search(r"قال\s+(تعالى|الله|تبارك|رسول|النبي|ابن)", clause):
            return True
        # إسناد لغوي: «قال سيبويه: …» — نقاش نحوي لا معنى
        if re.search(r"قال\s+[ء-ي]+\s*[::]", strip_diacritics(clause)):
            return True
        # حروف الجذر ملتصقة ببداية الشاهد: «كثبقال تعالى»
        if root_plain and strip_diacritics(clause).startswith(root_plain + "قال"):
            return True

        def _plain(t: str) -> str:
            return strip_diacritics(t).strip("و ف")

        toks = clause.split()
        # تعداد حروف الجذر: «س ن دالسنّد» أو «الخاء والشين والياء…»
        singles = sum(1 for t in toks[:4] if len(_plain(t)) <= 1)
        names = sum(1 for t in toks[:4] if re.fullmatch(r"[او]?ل?[ء-ي]اء", _plain(t)))
        # أسماء الحروف الصريحة: «السين والميم والواو س مو…»
        letter_names = {
            "الف",
            "الباء",
            "التاء",
            "الثاء",
            "الجيم",
            "الحاء",
            "الخاء",
            "الدال",
            "الذال",
            "الراء",
            "الزاي",
            "السين",
            "الشين",
            "الصاد",
            "الضاد",
            "الطاء",
            "الظاء",
            "العين",
            "الغين",
            "الفاء",
            "الكاف",
            "اللام",
            "الميم",
            "النون",
            "الهاء",
            "الواو",
            "الياء",
            "الهمزة",
        }
        explicit_names = sum(
            1
            for t in toks[:4]
            if _plain(t) in letter_names
            or _plain(t).lstrip("ا") in {n.lstrip("ا") for n in letter_names}
            and _plain(t).startswith("ال")
        )
        if singles >= 2 or explicit_names >= 2 or (names >= 1 and names >= singles):
            return True
        return False

    # أول سطرين معاً — رأس المادة قد ينكسر على سطرين
    lines = [clean_ws(l) for l in definition.splitlines() if l.strip()]
    if not lines:
        return None, "none"
    head = clean_ws(" ".join(lines[:2]))

    # إزالة تمهيد «باب ... » إذا بدأ به
    if head.startswith("باب"):
        rest = clean_ws(" ".join(lines[2:]))
        m = re.search(r"[:：]", rest)
        head = rest[m.end() :].strip() if m else rest
        if not head:
            return None, "none"

    root_plain = strip_diacritics(re.sub(r"\s+", "", root))

    def strip_root_prefix(text: str) -> tuple[str, bool]:
        """يشيل تكرار حروف الجذر في البداية («زور ال الكذب»←«ال الكذب»)."""
        stripped = strip_diacritics(text)
        i = matched = 0
        while i < len(stripped):
            ch = stripped[i]
            if ch == " " and matched > 0:
                i += 1
                break
            if ch in set(root_plain):
                matched += 1
                i += 1
            else:
                break
        ok = matched >= len(root_plain) - 1
        return (text[i:].strip(), ok) if ok else (text, False)

    # نمط (أ): «الحاشية: تعريف»
    m = re.search(r"[:：]", head)
    if m and m.start() < 80:
        clause = first_clause(head[m.end() :])
        if clause and not is_bad(clause):
            return cap_at_word(clause, MAX_AR), "colon"

    # نمط (ب): إزالة أقواس ثم أول جملة
    no_brackets = clean_ws(re.sub(r"\[[^\]]*\]", " ", head))
    stripped_ver, did_strip = strip_root_prefix(no_brackets)
    sentence = re.split(r"[.۔]", stripped_ver)[0].strip()
    clause = first_clause(sentence)
    if clause and not is_bad(clause):
        # إن كانت النتيجة قصيرة جداً بعد إزالة الجذر، جرّب بدون الإزالة
        if not did_strip or len(strip_diacritics(clause)) >= MIN_AR:
            trimmed = clause.lstrip("ًٌٍَُِّْ").strip()
            return cap_at_word(trimmed or clause, MAX_AR), "sentence"

    if did_strip:
        sentence2 = re.split(r"[.۔]", no_brackets)[0].strip()
        clause2 = first_clause(sentence2)
        if clause2 and not is_bad(clause2):
            return cap_at_word(clause2, MAX_AR), "sentence"

    # آخر محاولة: أول 120 حرفاً كما هي
    if len(strip_diacritics(head)) >= MIN_AR and not is_bad(head):
        return cap_at_word(head, MAX_AR), "extended"
    return None, "none"


AR_RANGE = "\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff"


def extract_english(definition: str) -> str | None:
    """
    من معجم لين: التعريف الجوهري غالباً داخل [] — نجربها أولاً،
    وإلا فأول جملة إنجليزية نظيفة بعد إزالة العربية والأقواس.
    """
    text = clean_ws(definition.replace("\n", " "))

    # المحاولة الأولى: محتوى أول قوس مربع يضم ٣ كلمات إنجليزية فأكثر
    for m in re.finditer(r"\[([^\]]+)\]", text):
        inner = clean_ws(re.sub(f"[{AR_RANGE}↓→]", " ", m.group(1)))
        words = [t for t in inner.split(" ") if len(re.sub(r"[^A-Za-z]", "", t)) >= 2]
        if len(words) >= 3:
            eng = cap_at_word(inner.split(":")[0].strip(" ,;"), MAX_EN)
            if len(re.sub(r"[^A-Za-z ]", "", eng)) >= 12:
                return eng

    # المحاولة الثانية: نص إنجليزي حر بعد إزالة الأقواس والعربية
    text2 = re.sub(r"\([^)]*\)", " ", text)
    text2 = re.sub(r"\[[^\]]*\]", " ", text2)
    text2 = re.sub(f"[{AR_RANGE}↓→*]", " ", text2)
    tokens = [t for t in clean_ws(text2).split(" ") if t.strip(",;:")]
    out = []
    stop_leading = {"and", "or", "of", "the", "a", "an", "to", "in", "with", "from"}
    for i, tok in enumerate(tokens):
        base = tok.strip(",;:")
        if not out and (
            base.lower() in stop_leading
            or len(base) <= 2
            or re.fullmatch(r"[a-z]{1,4}\.", base)
        ):
            continue
        if base.lower() == "and" and out and out[-1].lower() == "and":
            continue
        out.append(tok)
    eng = cap_at_word(clean_ws(" ".join(out)), MAX_EN).strip(",;")
    if len(re.sub(r"[^A-Za-z ]", "", eng)) < 12:
        return None
    return eng


def build(conn: sqlite3.Connection) -> dict:
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS root_glosses (
            root_id   INTEGER PRIMARY KEY REFERENCES roots(id),
            gloss_ar  TEXT,
            gloss_en  TEXT,
            ar_source TEXT,
            en_source TEXT
        )
        """
    )
    conn.commit()

    roots = cur.execute("SELECT id, root FROM roots ORDER BY id").fetchall()
    meanings: dict[int, dict[str, tuple[str, str]]] = {}
    for rid, book, dfn in cur.execute(
        "SELECT root_id, book_name, definition FROM root_meanings"
    ):
        meanings.setdefault(rid, {})[book] = (dfn or "",)

    lane: dict[int, tuple[str, str]] = {}
    for rid, book, dfn in cur.execute(
        "SELECT root_id, book_name, definition FROM root_meanings WHERE book_name LIKE ?",
        (EN_BOOK_LIKE,),
    ):
        lane[rid] = (dfn or "", book)

    stats = {"total": len(roots), "ar": 0, "en": 0, "methods": {}}
    rows = []
    for rid, root in roots:
        gloss_ar = src_ar = method = None
        books = meanings.get(rid, {})
        for book in AR_BOOKS:
            entry = books.get(book)
            if not entry:
                continue
            g, method = extract_arabic(entry[0], root)
            if g:
                gloss_ar, src_ar = g, book
                break
        if gloss_ar:
            stats["ar"] += 1
        stats["methods"][method or "missing"] = (
            stats["methods"].get(method or "missing", 0) + 1
        )

        gloss_en = src_en = None
        if rid in lane:
            dfn, book = lane[rid]
            g = extract_english(dfn)
            if g:
                gloss_en, src_en = g, book
        if gloss_en:
            stats["en"] += 1

        rows.append((rid, gloss_ar, gloss_en, src_ar, src_en))

    cur.executemany("INSERT OR REPLACE INTO root_glosses VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    return stats


def show_samples(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    print("\n=== عينات للمراجعة ===")
    for root in ["زور", "كتب", "رحم", "علم", "سلم", "قمر", "هدي"]:
        row = cur.execute(
            """
            SELECT r.root, g.gloss_ar, g.gloss_en, g.ar_source
            FROM root_glosses g JOIN roots r ON r.id = g.root_id
            WHERE r.root = ?
            """,
            (root,),
        ).fetchone()
        if row:
            print(f"[{row[0]}]")
            print(f"  AR: {row[1]}")
            print(f"  EN: {row[2]}")
            print(f"  المصدر: {row[3]}")
        else:
            print(f"[{root}] لا يوجد")


def random_sample(conn: sqlite3.Connection, n: int = 15) -> None:
    cur = conn.cursor()
    print("\n=== عينة عشوائية (لمراجعة الجودة) ===")
    for row in cur.execute(
        """
        SELECT r.root, g.gloss_ar, LENGTH(g.gloss_ar), g.ar_source
        FROM root_glosses g JOIN roots r ON r.id = g.root_id
        WHERE g.gloss_ar IS NOT NULL
        ORDER BY RANDOM() LIMIT ?
        """,
        (n,),
    ):
        flag = "⚠️" if (row[2] or 0) > MAX_AR else " "
        print(f"{flag} [{row[0]}] ({row[2]}ح، {row[3][:20]}…): {row[1]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", action="store_true", help="عرض عينات بعد البناء")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    stats = build(conn)

    print("=== تقرير بناء root_glosses ===")
    print(f"إجمالي الجذور: {stats['total']}")
    ar_pct = stats["ar"] / stats["total"] * 100
    en_pct = stats["en"] / stats["total"] * 100
    print(f"معنى عربي مختصر: {stats['ar']} ({ar_pct:.0f}%)")
    print(f"معنى إنجليزي مختصر: {stats['en']} ({en_pct:.0f}%)")
    print("طرق الاستخراج:", stats["methods"])

    show_samples(conn)
    random_sample(conn)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
