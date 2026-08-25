#!/usr/bin/env python3
"""
تصدير حزم تعريفات المعاجم لكل جذر — ملف نصي واحد لكل جذر
Stage: Export root_meanings bundles for AI summarization.

لكل جذر له تعريفات في root_meanings يُكتب ملف:
  {out_dir}/{root}.txt
بترويسة «# جذر: ...» وكل معجم تحت عنوان «## اسم الكتاب» مفصولاً بـ«---».

الاستعمال:
  python scripts/export_root_bundles.py                     # كل الجذور
  python scripts/export_root_bundles.py --roots "نحل,كتب"   # جذور محددة
  python scripts/export_root_bundles.py --list              # عرض الجذور فقط

الخرج الافتراضي: /tmp/opencode/root_bundles/
"""

import argparse
import sqlite3
import sys
import textwrap
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"

DEFAULT_OUT = Path("/tmp/opencode/root_bundles")

BOOK_ORDER = [
    "المفردات في غريب القرآن للراغب الأصفهاني",
    "المحكم والمحيط الأعظم لابن سيده الأندلسي",
    "تاج اللغة وصِحاح العربية للجوهري",
    "أساس البلاغة للزمخشري",
    "كتاب العين للخليل بن أحمد الفراهيدي",
    "لسان العرب لابن منظور",
    "تاج العروس لمرتضى الزبيدي",
    "المعجم العربي الإنجليزي",
]


def fetch_roots(cur, only=None):
    sql = """
        SELECT r.id, r.root, COUNT(m.id), SUM(LENGTH(m.definition)), MIN(m.definition)
        FROM roots r JOIN root_meanings m ON m.root_id = r.id
    """
    args = []
    if only:
        roots = [r.strip() for r in only.split(",") if r.strip()]
        sql += f" WHERE r.root IN ({','.join('?' * len(roots))})"
        args = roots
    sql += " GROUP BY r.id ORDER BY r.id"
    return cur.execute(sql, args).fetchall()


def export_bundle(cur, root_id, root_text, out_dir):
    rows = cur.execute(
        "SELECT book_name, source_url, definition FROM root_meanings WHERE root_id = ?",
        (root_id,),
    ).fetchall()
    by_book = {}
    for book, url, definition in rows:
        by_book.setdefault(book or "غير معروف", []).append((url, definition))

    ordered = [b for b in BOOK_ORDER if b in by_book]
    ordered += [b for b in by_book if b not in BOOK_ORDER]

    parts = [f"# جذر: {root_text}  (root_id={root_id})\n"]
    for i, book in enumerate(ordered):
        if i:
            parts.append("\n---\n")
        parts.append(f"\n## {book}\n")
        for url, definition in by_book[book]:
            wrapped = textwrap.fill(definition.strip(), width=300)
            parts.append(f"\n{wrapped}\n")
            if url:
                parts.append(f"\n(المصدر: {url})\n")

    path = out_dir / f"{root_text}.txt"
    path.write_text("".join(parts), encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", help="جذور محددة مفصولة بفواصل مثل: نحل,كتب")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--list", action="store_true", help="عرض الجذور دون تصدير")
    ns = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    rows = fetch_roots(cur, ns.roots)

    if ns.list:
        for _id, root, n_books, chars, _ in rows:
            print(f"{root}\tbooks={n_books}\tchars={chars}")
        return 0

    ns.out.mkdir(parents=True, exist_ok=True)
    total_chars = 0
    for root_id, root, n_books, chars, _ in rows:
        export_bundle(cur, root_id, root, ns.out)
        total_chars += chars or 0
        print(f"[ok] {root}: {n_books} معاجم، {chars} حرف")

    print(f"\nتم تصدير {len(rows)} جذر ({total_chars} حرف) إلى {ns.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
