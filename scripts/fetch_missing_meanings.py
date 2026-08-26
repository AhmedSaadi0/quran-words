#!/usr/bin/env python3
"""
جلب المعاني الناقصة للجذور المصححة من arabic_roots.json و hawramani
Stage: Fetch missing meanings for corrected roots.

يقرأ data/roots_verification.csv ويجلب لكل جذر مُصحح:
 - من arabic_roots.json بالجذر المصحح
 - إن لم يوجد، يُسجل للجلب اليدوي من hawramani

ثم يُحدّث quran_words.db:root_meanings و roots (عند الثقة العالية)
"""

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "quran_words.db"
ARABIC_JSON = Path(__file__).resolve().parent.parent / "data" / "arabic_roots.json"
VERIF_CSV = Path(__file__).resolve().parent.parent / "data" / "roots_verification.csv"


def load_arabic():
    if not ARABIC_JSON.exists():
        return {}
    return json.loads(ARABIC_JSON.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="تطبيق التحديث على قاعدة البيانات فعلاً (بدونه معاينة فقط)",
    )
    parser.add_argument(
        "--min-confidence", type=float, default=0.90, help="أدنى ثقة لتحديث roots.root"
    )
    ns = parser.parse_args()

    arabic = load_arabic()
    print(f"arabic_roots.json: {len(arabic)} مفتاح")

    # قراءة التحقق
    rows = list(csv.DictReader(open(VERIF_CSV, encoding="utf-8")))
    to_fetch = [r for r in rows if r["status"].startswith("مُصحح")]
    print(f"جذور مُصححة تحتاج جلب: {len(to_fetch)} من {len(rows)}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    fetched = 0
    would_update_roots = 0
    would_insert_meanings = 0
    report = []

    for r in to_fetch:
        stored = r["root_stored"]
        corrected = r["root_corrected"]
        rid = int(r["root_id"])
        conf = float(r["confidence"])

        # هل المصحح له مادة في arabic_roots.json ؟
        entries = arabic.get(corrected)
        if not entries:
            # جرب بدون همزة (بعض المعاجم تفهرس بدون همزة)
            # مثلاً أله قد يكون تحت له
            alt = corrected.lstrip("ءأإآ")
            entries = arabic.get(alt) or arabic.get(corrected.replace("ء", ""))
        if entries:
            # entries is list of {definition, book_name, url}
            existing_cnt = cur.execute(
                "SELECT COUNT(*) FROM root_meanings WHERE root_id=?", (rid,)
            ).fetchone()[0]
            report.append(
                f"[found] {stored}→{corrected}: {len(entries)} مادة في arabic_roots.json (حالياً {existing_cnt} في DB)"
            )
            fetched += 1
            would_insert_meanings += len(entries)
            if conf >= ns.min_confidence:
                # تحقق هل roots.root الحالي هو المخزن وهل المصحح مختلف
                current = cur.execute(
                    "SELECT root FROM roots WHERE id=?", (rid,)
                ).fetchone()[0]
                if current == stored and stored != corrected:
                    would_update_roots += 1
                    report.append(
                        f"  → سيُحدَّث roots.root: '{stored}' → '{corrected}' (ثقة {conf})"
                    )

            if ns.apply:
                # أدخل المعاني إن لم تكن موجودة (تجنب التكرار بالـ book_name+definition)
                for e in entries:
                    definition = e.get("definition", "").strip()
                    book = e.get("book_name", "").strip()
                    url = e.get("url", "").strip()
                    if not definition:
                        continue
                    exists = cur.execute(
                        "SELECT 1 FROM root_meanings WHERE root_id=? AND book_name=? AND definition=?",
                        (rid, book, definition),
                    ).fetchone()
                    if not exists:
                        cur.execute(
                            "INSERT INTO root_meanings (root_id, definition, book_name, source_url) VALUES (?,?,?,?)",
                            (rid, definition, book, url),
                        )
                # حدّث roots.root إذا لزم
                if conf >= ns.min_confidence:
                    current = cur.execute(
                        "SELECT root FROM roots WHERE id=?", (rid,)
                    ).fetchone()[0]
                    if current == stored and stored != corrected:
                        cur.execute(
                            "UPDATE roots SET root=? WHERE id=?", (corrected, rid)
                        )
        else:
            report.append(
                f"[missing] {stored}→{corrected}: لا مادة في arabic_roots.json — يحتاج hawramani يدوياً أو سيُلخص من السياق"
            )

    for line in report:
        print(line)

    print(f"\nالملخص: وُجدت مادة لـ {fetched}/{len(to_fetch)} جذراً مُصححاً")
    print(f"  صفوف root_meanings ستُضاف: ~{would_insert_meanings}")
    print(f"  جذور roots ستُصحح: {would_update_roots} (بثقة ≥{ns.min_confidence})")

    if ns.apply:
        con.commit()
        # بعد التحديث، أعد تصدير الحزم للجذور المصححة
        corrected_list = [
            r["root_corrected"]
            for r in to_fetch
            if arabic.get(r["root_corrected"])
            or arabic.get(r["root_corrected"].lstrip("ءأإآ"))
        ]
        print(f"\nتم التطبيق. لإعادة تصدير الحزم:")
        print(
            f'  python scripts/export_root_bundles.py --roots "{",".join(corrected_list[:5])}..."'
        )
        # حدّث roots_without_meanings.json
        remaining = cur.execute("""
            SELECT r.root FROM roots r
            LEFT JOIN root_meanings m ON m.root_id=r.id
            GROUP BY r.id HAVING COUNT(m.id)=0
        """).fetchall()
        print(f"  جذور بلا معانٍ بعد التحديث: {len(remaining)} (كانت 62)")
    else:
        print("\nوضع المعاينة فقط — لم يُطبَّق على DB. استخدم --apply للتطبيق.")
        con.rollback()

    return 0


if __name__ == "__main__":
    sys.exit(main())
