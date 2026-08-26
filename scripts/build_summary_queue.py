#!/usr/bin/env python3
"""
بناء طابور دفعات تلخيص الجذور بالذكاء الاصطناعي
Stage: Build summarization queue ordered by Quranic frequency.

يرتب الجذور التي لها معاجم تنازلياً بحسب تكرارها في القرآن (word_morphology)،
ويستثني ما لُخِّص مسبقاً في data/root_ai_summary.json، ثم يجمعها دفعات:
  - حجم الدفعة المستهدف: ~160K حرف تعريفات (حد أعلى 200K)
  - حد أقصى 12 جذراً للدفعة

الخرج: /tmp/opencode/summary_queue.json — قائمة دفعات، كل دفعة قائمة جذور.

الاستعمال:
  python scripts/build_summary_queue.py [--target-chars 160000] [--max-roots 12]
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"
SUMMARY_JSON = Path(__file__).resolve().parent.parent / "data" / "root_ai_summary.json"
QUEUE_PATH = Path("/tmp/opencode/summary_queue.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-chars", type=int, default=160_000)
    parser.add_argument("--max-roots", type=int, default=12)
    ns = parser.parse_args()

    done = set()
    pending = 0
    data = {}
    if SUMMARY_JSON.exists():
        data = json.loads(SUMMARY_JSON.read_text())
        # JSON الآن يحوي كل الجذور (1642) مع summary_ar = null للمُعلّق؛
        # نعتبر "مُنجزاً" فقط ما له ملخص غير فارغ
        done = {
            root
            for root, entry in data.items()
            if (isinstance(entry, dict) and entry.get("summary_ar"))
            or (isinstance(entry, str) and entry.strip())
        }
        pending = len(data) - len(done)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    not_in = ""
    args: list = []
    if done:
        not_in = f" AND r.root NOT IN ({','.join('?' * len(done))})"
        args = list(done)
    rows = cur.execute(
        f"""
        SELECT r.root,
               COALESCE(SUM(LENGTH(m.definition)), 0) AS chars,
               COALESCE(freq.n, 0) AS quran_count
        FROM roots r
        LEFT JOIN root_meanings m ON m.root_id = r.id
        LEFT JOIN (
            SELECT rm.id AS root_id, COUNT(*) AS n
            FROM word_morphology wm JOIN roots rm ON rm.id = wm.root_id
            GROUP BY rm.id
        ) freq ON freq.root_id = r.id
        GROUP BY r.id
        HAVING chars > 0{not_in}
        ORDER BY quran_count DESC, chars DESC
        """,
        args,
    ).fetchall()

    batches = []
    current, size = [], 0
    for root, chars, _freq in rows:
        if current and (size + chars > ns.target_chars or len(current) >= ns.max_roots):
            batches.append(current)
            current, size = [], 0
        current.append(root)
        size += chars
    if current:
        batches.append(current)

    QUEUE_PATH.write_text(json.dumps(batches, ensure_ascii=False, indent=1))
    total = sum(len(b) for b in batches)
    print(f"remaining roots: {total} in {len(batches)} batches -> {QUEUE_PATH}")
    print(
        f"done so far: {len(done)} | pending in JSON (null): {pending if SUMMARY_JSON.exists() else 0}"
    )
    for i, b in enumerate(batches[:5]):
        print(f"  batch[{i}]: {b}")


if __name__ == "__main__":
    sys.exit(main())
