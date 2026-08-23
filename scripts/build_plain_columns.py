#!/usr/bin/env python3
"""
بناء الأعمدة المطبّعة للبحث السريع
Stage: Add normalized search columns.

المشكلة: النصوص في DB مشكولة («ٱللَّهِ») والبحث icontains بالنص العادي
(«الله») لا يجدها. الحل: عمودان مطبّعان بنفس دالة التطبيع المستخدمة في
الاستعلام (core.utils.normalize_ar):
  - words.text_plain            من words.text
  - ayat.text_uthmani_plain     من ayat.text_uthmani

إضافة آمنة فقط (ALTER TABLE ADD COLUMN) — idempotent.
الاستعمال:
  python scripts/build_plain_columns.py
"""

import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"

DIACRITICS_RE = re.compile(
    r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]"
)


def normalize_ar(s: str) -> str:
    """مطابقة لـ backend/core/utils.py:normalize_ar"""
    if not s:
        return ""
    s = DIACRITICS_RE.sub("", s)
    s = (
        s.replace("ٱ", "ا")
        .replace("ـ", "")
        .replace("آ", "ا")
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("ى", "ي")
    )
    return s.strip()


def column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    return any(r[1] == col for r in cur.execute(f"PRAGMA table_info({table})"))


def add_plain_column(
    conn: sqlite3.Connection,
    table: str,
    source_col: str,
    plain_col: str,
) -> int:
    cur = conn.cursor()
    if not column_exists(cur, table, plain_col):
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {plain_col} TEXT")
        action = "أُنشئ"
    else:
        action = "موجود — حُدّث"

    rows = cur.execute(f"SELECT rowid, {source_col} FROM {table}").fetchall()
    updates = [(normalize_ar(src or ""), rid) for rid, src in rows]
    cur.executemany(f"UPDATE {table} SET {plain_col} = ? WHERE rowid = ?", updates)
    conn.commit()
    return len(updates), action


def main() -> int:
    conn = sqlite3.connect(DB_PATH)

    n1, a1 = add_plain_column(conn, "words", "text", "text_plain")
    print(f"[words] text_plain: {n1} صف — العمود {a1}")

    n2, a2 = add_plain_column(conn, "ayat", "text_uthmani", "text_uthmani_plain")
    print(f"[ayat] text_uthmani_plain: {n2} صف — العمود {a2}")

    # عينات تحقق
    cur = conn.cursor()
    for label, sql in [
        ("كتاب →", "SELECT text FROM words WHERE text_plain LIKE '%كتاب%' LIMIT 3"),
        (
            "الله →",
            "SELECT SUBSTR(text_uthmani,1,40) FROM ayat WHERE text_uthmani_plain LIKE '%ان الله%' LIMIT 2",
        ),
    ]:
        rows = cur.execute(sql).fetchall()
        print(f"\n{label}")
        for r in rows:
            print(" ", r[0])

    conn.close()
    print("\nتم ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
