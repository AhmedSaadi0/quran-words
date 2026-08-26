#!/usr/bin/env python3
"""
تصدير أدلة شاملة لكل الجذور (1,642) مع الملخص الحالي
Stage: Export verification evidence for ALL roots.

لكل جذر يجلب:
 - كل الآيات المرتبطة (عينة 5) + الكلمات/اللمّات
 - المعاني الحالية (عينة) + الملخص الحالي

الخرج: data/verify_all/{root}.json (1,642) + index.json
"""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "verify_all"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    roots = [r[0] for r in cur.execute("SELECT root FROM roots ORDER BY id").fetchall()]
    print(f"تصدير {len(roots)} جذراً...")

    # تحميل الملخصات الحالية
    try:
        summaries = json.loads(
            (
                Path(__file__).resolve().parent.parent / "data" / "root_ai_summary.json"
            ).read_text(encoding="utf-8")
        )
    except Exception:
        summaries = {}

    index = []
    for root in roots:
        rid = cur.execute("SELECT id FROM roots WHERE root=?", (root,)).fetchone()[0]
        occ = cur.execute(
            "SELECT COUNT(*) FROM word_morphology WHERE root_id=?", (rid,)
        ).fetchone()[0]
        meanings_cnt = cur.execute(
            "SELECT COUNT(*) FROM root_meanings WHERE root_id=?", (rid,)
        ).fetchone()[0]

        distinct = cur.execute(
            """
            SELECT w.text, l.lemma_ar, COUNT(*) c
            FROM word_morphology wm
            JOIN word_ayah wa ON wa.id=wm.word_ayah_id
            JOIN words w ON w.id=wa.word_id
            LEFT JOIN lemmas l ON l.id=wm.lemma_id
            WHERE wm.root_id=?
            GROUP BY w.text, l.lemma_ar
            ORDER BY c DESC LIMIT 5
        """,
            (rid,),
        ).fetchall()
        distinct_words = [{"word": w, "lemma": l, "count": c} for w, l, c in distinct]

        ayat_rows = cur.execute(
            """
            SELECT w.text, l.lemma_ar, a.surah, a.ayah, a.text_uthmani
            FROM word_morphology wm
            JOIN word_ayah wa ON wa.id=wm.word_ayah_id
            JOIN words w ON w.id=wa.word_id
            JOIN ayat a ON a.id=wa.ayah_id
            LEFT JOIN lemmas l ON l.id=wm.lemma_id
            WHERE wm.root_id=?
            ORDER BY a.surah, a.ayah LIMIT 5
        """,
            (rid,),
        ).fetchall()
        ayat = [
            {
                "word": w,
                "lemma": l,
                "surah": s,
                "ayah": ay,
                "ayah_text": uth[:80] if uth else "",
            }
            for w, l, s, ay, uth in ayat_rows
        ]

        meanings_sample = cur.execute(
            "SELECT book_name, SUBSTR(definition,1,150) FROM root_meanings WHERE root_id=? LIMIT 2",
            (rid,),
        ).fetchall()
        meanings_sample = [{"book": b, "snippet": d} for b, d in meanings_sample]

        summary_entry = summaries.get(root, {})
        ai_summary = (
            summary_entry.get("summary_ar")
            if isinstance(summary_entry, dict)
            else summary_entry
        )
        ai_model = (
            summary_entry.get("model") if isinstance(summary_entry, dict) else None
        )

        obj = {
            "root": root,
            "root_id": rid,
            "quran_occurrences": occ,
            "meanings_count": meanings_cnt,
            "meanings_sample": meanings_sample,
            "distinct_words": distinct_words,
            "ayat_sample": ayat,
            "ai_summary_ar": ai_summary,
            "ai_model": ai_model,
            "has_summary": bool(ai_summary),
        }
        (OUT_DIR / f"{root}.json").write_text(
            json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        index.append(
            {
                "root": root,
                "root_id": rid,
                "occurrences": occ,
                "meanings": meanings_cnt,
                "has_summary": bool(ai_summary),
            }
        )

    Path(OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"تم تصدير {len(index)} حزمة إلى {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
