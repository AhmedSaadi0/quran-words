#!/usr/bin/env python3
"""
بناء/تحديث جدول الملخصات المولدة بالذكاء الاصطناعي لكل جذر
Stage: Load data/root_ai_summary.json into quran_words.db

ينشئ الجدول root_ai_summary إن لم يكن موجوداً ثم يحمّل/يحدّث الملخصات.
الملخصات بتوليف كل معاني المعاجم للجذر الواحد (عربي فقط، مع تشكيل وافٍ).

الاستعمال:
  python scripts/build_root_ai_summary.py              # تحميل كامل
  python scripts/build_root_ai_summary.py --dry-run    # معاينة فقط
  python scripts/build_root_ai_summary.py --stats      # إحصائيات فقط
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"
JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "root_ai_summary.json"


DDL = """
CREATE TABLE IF NOT EXISTS root_ai_summary (
    root_id      INTEGER PRIMARY KEY REFERENCES roots(id),
    summary_ar   TEXT NOT NULL,
    model        TEXT,
    generated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_root_ai_summary_model ON root_ai_summary(model);
"""


def _fallback_model() -> str:
    """احتياط ديناميكي — يُستخدم فقط للدفعات القديمة بصيغة string بلا حقل model."""
    import os

    for key in ("OPENCODE_MODEL", "MODEL", "LLM_MODEL"):
        if os.environ.get(key):
            return os.environ[key].strip()
    p = JSON_PATH.parent / "current_model.txt"
    if p.exists():
        try:
            txt = p.read_text(encoding="utf-8").strip()
            if txt:
                return txt
        except Exception:
            pass
    return "muse-spark-1.2-contributor-free"


def load_json():
    if not JSON_PATH.exists():
        print(f"لا يوجد ملف: {JSON_PATH}", file=sys.stderr)
        return {}
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="معاينة دون كتابة")
    parser.add_argument("--stats", action="store_true", help="إحصائيات فقط")
    ns = parser.parse_args()

    data = load_json()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(DDL)

    total_in_db = cur.execute("SELECT COUNT(*) FROM root_ai_summary").fetchone()[0]
    total_roots = cur.execute("SELECT COUNT(*) FROM roots").fetchone()[0]
    roots_with_meanings = cur.execute(
        "SELECT COUNT(DISTINCT root_id) FROM root_meanings"
    ).fetchone()[0]

    if ns.stats:
        print(
            f"roots: {total_roots} | with_meanings: {roots_with_meanings} | ai_summary rows: {total_in_db} | json entries: {len(data)}"
        )
        # sample
        for row in cur.execute(
            "SELECT r.root, SUBSTR(s.summary_ar,1,80) FROM root_ai_summary s JOIN roots r ON r.id=s.root_id LIMIT 3"
        ):
            print(f"  {row[0]}: {row[1]}...")
        return 0

    if not data:
        print("JSON فارغ — لا شيء للتحميل")
        return 0

    # map root text -> id
    root_ids = {
        root_text: rid for root_text, rid in cur.execute("SELECT root, id FROM roots")
    }
    missing = [k for k in data if k not in root_ids]
    if missing:
        print(f"تحذير: {len(missing)} جذر في JSON غير موجود في roots: {missing[:5]}")

    rows = []
    for root_text, entry in data.items():
        rid = root_ids.get(root_text)
        if rid is None:
            continue
        # entry may be {"summary_ar":..., "model":..., "generated_at":...} or plain string (legacy)
        # الموديل يُكتب من الوكيل نفسه في الحقل model داخل الـ dict — لا يُؤخذ نص جاهز من الخطة
        if isinstance(entry, str):
            summary, model, gen = entry, _fallback_model(), None
        else:
            summary = entry.get("summary_ar") or entry.get("summary") or ""
            model = entry.get("model") or _fallback_model()
            gen = entry.get("generated_at")
        if not summary:
            continue
        rows.append((rid, summary.strip(), model, gen))

    if ns.dry_run:
        print(f"dry-run: سيتم تحميل {len(rows)} صف (حالياً {total_in_db})")
        return 0

    cur.executemany(
        "INSERT OR REPLACE INTO root_ai_summary(root_id, summary_ar, model, generated_at) VALUES (?,?,?,?)",
        rows,
    )
    con.commit()
    new_total = cur.execute("SELECT COUNT(*) FROM root_ai_summary").fetchone()[0]
    print(
        f"تم: {len(rows)} صف محمّل -> الإجمالي {new_total} (كان {total_in_db}) | JSON entries: {len(data)}"
    )
    # تقرير تغطية
    uncovered = roots_with_meanings - new_total
    if uncovered > 0:
        print(f"متبقي بلا ملخص AI: {uncovered} جذراً لها معانٍ في root_meanings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
