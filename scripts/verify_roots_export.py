#!/usr/bin/env python3
"""
تصدير أدلة آيات لكل جذر يحتاج تحققاً (الـ68 التي تبدأ بـ ى + الـ19 المتبقية بلا معانٍ = 87 جذراً)
Stage: Export verification evidence for roots needing review.

لكل جذر يجلب:
 - كل الآيات المرتبطة عبر roots → word_morphology → word_ayah → words → ayat
 - الكلمات المميزة واللمّات
 - مطابقة arabic_roots.json ومقترحات hawramani

الخرج: data/verify_roots/{root}.json  (87 ملفاً) + ملخص data/verify_roots/index.json
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"
ARABIC_ROOTS_JSON = (
    Path(__file__).resolve().parent.parent / "data" / "arabic_roots.json"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "verify_roots"


def get_target_roots(cur):
    # 68 تبدأ بـ ى
    ya_roots = [
        r[0]
        for r in cur.execute(
            "SELECT root FROM roots WHERE root LIKE 'ى%' ORDER BY id"
        ).fetchall()
    ]
    # 62 بلا معانٍ
    without = [
        r[0]
        for r in cur.execute("""
        SELECT r.root FROM roots r
        LEFT JOIN root_meanings m ON m.root_id=r.id
        GROUP BY r.id HAVING COUNT(m.id)=0
    """).fetchall()
    ]
    union = sorted(
        set(ya_roots + without), key=lambda x: (0 if x.startswith("ى") else 1, x)
    )
    # لكن نريد ترتيباً بـ id الأصلي للحفاظ على التسلسل القرآني
    # نحصل على id لكل
    id_map = {r: i for i, r in cur.execute("SELECT root, id FROM roots")}
    union_sorted = sorted(set(ya_roots + without), key=lambda r: id_map.get(r, 9999))
    return union_sorted, ya_roots, without


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # تحميل مفاتيح arabic_roots.json للتحقق
    arabic_keys = set()
    if ARABIC_ROOTS_JSON.exists():
        try:
            arabic_keys = set(
                json.loads(ARABIC_ROOTS_JSON.read_text(encoding="utf-8")).keys()
            )
        except Exception as e:
            print(f"تحذير: فشل قراءة arabic_roots.json: {e}", file=sys.stderr)

    targets, ya_roots, without = get_target_roots(cur)
    print(
        f"نطاق التحقق: {len(targets)} جذراً فريداً (68 تبدأ بـ ى + 19 أخرى بلا معانٍ لا تبدأ بـ ى)"
    )
    print(f"  - تبدأ بـ ى: {len(ya_roots)}")
    print(f"  - بلا معانٍ: {len(without)} (منها 43 تبدأ بـ ى)")
    print(f"  - الاتحاد: {len(targets)}")

    index = []
    for root in targets:
        row = cur.execute("SELECT id FROM roots WHERE root=?", (root,)).fetchone()
        if not row:
            print(f"[skip] {root} غير موجود في roots", file=sys.stderr)
            continue
        rid = row[0]
        # occurrences
        occ = cur.execute(
            "SELECT COUNT(*) FROM word_morphology WHERE root_id=?", (rid,)
        ).fetchone()[0]
        # distinct words / lemmas
        distinct = cur.execute(
            """
            SELECT w.text, w.text_clean, l.lemma_ar, COUNT(*) c
            FROM word_morphology wm
            JOIN word_ayah wa ON wa.id=wm.word_ayah_id
            JOIN words w ON w.id=wa.word_id
            LEFT JOIN lemmas l ON l.id=wm.lemma_id
            WHERE wm.root_id=?
            GROUP BY w.text, l.lemma_ar
            ORDER BY c DESC
            LIMIT 20
        """,
            (rid,),
        ).fetchall()
        distinct_words = [
            {"word": w, "clean": c, "lemma": l, "count": n} for w, c, l, n in distinct
        ]

        # sample ayat (up to 10)
        ayat_rows = cur.execute(
            """
            SELECT w.text, w.text_clean, l.lemma_ar, a.surah, a.ayah, a.text_uthmani, a.text_imlaei
            FROM word_morphology wm
            JOIN word_ayah wa ON wa.id=wm.word_ayah_id
            JOIN words w ON w.id=wa.word_id
            JOIN ayat a ON a.id=wa.ayah_id
            LEFT JOIN lemmas l ON l.id=wm.lemma_id
            WHERE wm.root_id=?
            ORDER BY a.surah, a.ayah
            LIMIT 10
        """,
            (rid,),
        ).fetchall()
        ayat = []
        for wtext, clean, lemma, surah, ayah, uth, iml in ayat_rows:
            ayat.append(
                {
                    "word": wtext,
                    "word_clean": clean,
                    "lemma": lemma,
                    "surah": surah,
                    "ayah": ayah,
                    "ayah_text_uthmani": uth,
                    "ayah_text_imlaei": iml,
                }
            )

        # check arabic_roots.json match
        arabic_match = root in arabic_keys
        # also try normalized variants (replace ى with ء/أ)
        variants = []
        if root.startswith("ى"):
            for repl in ["ء", "أ", "إ", "آ"]:
                cand = repl + root[1:]
                if cand in arabic_keys:
                    variants.append(cand)

        # meanings count currently
        meanings_cnt = cur.execute(
            "SELECT COUNT(*) FROM root_meanings WHERE root_id=?", (rid,)
        ).fetchone()[0]

        obj = {
            "root_stored": root,
            "root_id": rid,
            "starts_with_ya": root.startswith("ى"),
            "quran_occurrences": occ,
            "meanings_count_current": meanings_cnt,
            "distinct_words": distinct_words,
            "distinct_words_count": len(distinct),
            "ayat_sample": ayat,
            "ayat_sample_count": len(ayat),
            "arabic_roots_json_match": arabic_match,
            "arabic_roots_variants_found": variants,
            "needs_verification": True,
            "verification_hint": (
                "يبدأ بـ ى — تحقق هل الجذر الحقيقي للكلمات في الآيات هو نفسه أم همزة (ء/أ) — قارن اللمّة والكلمة"
                if root.startswith("ى")
                else "بلا معانٍ رغم عدم بدئه بـ ى — تحقق من صحة الجذر (مثل دمو→دم)"
            ),
        }
        out_path = OUT_DIR / f"{root}.json"
        out_path.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append(
            {
                "root": root,
                "root_id": rid,
                "occurrences": occ,
                "meanings": meanings_cnt,
                "starts_with_ya": root.startswith("ى"),
                "arabic_match": arabic_match,
                "variants": variants,
                "distinct_words_top": [d["word"] for d in distinct_words[:3]],
            }
        )
        print(
            f"[ok] {root} (id={rid}) occ={occ} meanings={meanings_cnt} arabic_match={arabic_match} variants={variants}"
        )

    # index
    Path(OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    # also CSV for quick review
    import csv

    with open(OUT_DIR / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "root",
                "root_id",
                "occurrences",
                "meanings",
                "starts_with_ya",
                "arabic_match",
                "variants",
                "distinct_words_top",
            ],
        )
        w.writeheader()
        for row in index:
            row2 = dict(row)
            row2["variants"] = ",".join(row2["variants"])
            row2["distinct_words_top"] = ",".join(row2["distinct_words_top"])
            w.writerow(row2)
    print(f"\nتم تصدير {len(index)} حزمة إلى {OUT_DIR}")
    print(f"  index.json + index.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
