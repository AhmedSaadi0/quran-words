#!/usr/bin/env python3
"""
إعادة التحقق من صحة الجذور الـ87 (68 تبدأ بـ ى + 19 بلا معانٍ أخرى)
Stage: Classify each root as صحيح / مُصحح / مُركب / علم

يقرأ data/verify_roots/*.json ويقارن:
 - الجذر المخزن vs arabic_roots.json (مفتاح + variants)
 - اللمّة والكلمات في الآيات
 - عدد المعاني الحالي

الخرج: data/roots_verification.csv + data/verify_roots/report.md
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

VERIFY_DIR = Path(__file__).resolve().parent.parent / "data" / "verify_roots"
OUT_CSV = Path(__file__).resolve().parent.parent / "data" / "roots_verification.csv"
OUT_REPORT = VERIFY_DIR / "report.md"

# قواعد تطبيع مبسطة
YA_TO_HAMZA = {
    "ىله": ("أله", "اسم الجلالة — مادة أله/وله/إله"),
    "ىخر": ("ءخر", "آخر — همزة على كرسي الياء"),
    "ىتي": ("ءتي", "أتى — همزة قطع"),
    "ىخذ": ("ءخذ", "أخذ"),
    "ىكل": ("ءكل", "أكل"),
    "ىمن": ("أمن", "آمن/أمن — همزة أصلية، لكن QAC يطبعها ىمن"),
    "ىنس": ("أنس", "أنس/نوس — الإنسان"),
    "ىبي": ("ءبي", "أبى"),
    "دمو": ("دم", "دم — واو زائدة"),
    "بوى": ("بوأ", "باء — واو مهموزة"),
}

# جذور لا مادة معجمية متوقعة (أعلام/نوادر)
NO_MATERIAL_EXPECTED = {
    "ىله",
    "حصحص",
    "زلزل",
    "رفرف",
    "ذبذب",
    "صلصل",
    "صفصف",
    "لىلى",
    "هدهد",
}


def classify(root: str, info: dict) -> tuple[str, str, float]:
    """
    Returns (status, corrected_root, confidence)
    status: صحيح | مُصحح | مُركب/مُفكك | علم
    """
    occ = info["quran_occurrences"]
    meanings = info["meanings_count_current"]
    variants = info["arabic_roots_variants_found"]
    distinct_top = [d["word"] for d in info["distinct_words"][:3]]

    # حالة خاصة: جذور الهمزة المصححة المعروفة
    if root in YA_TO_HAMZA:
        corr, note = YA_TO_HAMZA[root]
        # إذا كان الجذر له معانٍ فعلاً (مثل ىمن له 7) فقد يكون التطبيع مقصوداً في QAC — نتركه صحيحاً مع ملاحظة
        if meanings > 0 and root == "ىمن":
            return ("صحيح (تطبيع QAC مقصود)", root, 0.85)
        return ("مُصحح", corr, 0.95)

    # جذور تبدأ بـ ى ولها variants في arabic_roots.json → مُصحح
    if root.startswith("ى") and variants:
        # خذ أول variant كتصحيح مقترح
        return ("مُصحح", variants[0], 0.90)

    # جذور بلا معانٍ وتوقع لا مادة
    if root in NO_MATERIAL_EXPECTED:
        if meanings == 0:
            return ("علم/لا مادة معجمية متوقعة", root, 0.80)
        return ("صحيح", root, 0.85)

    # حالة ىذن المركبة
    if root == "ىذن":
        return ("مُركب/مُفكك", "أذن+إذن", 0.88)

    # إذا كان الجذر يبدأ بـ ى وبلا معانٍ وبلا variants → مُصحح محتمل بهمزة
    if root.startswith("ى") and meanings == 0 and not variants:
        # اقترح همزة قطع
        cand = "أ" + root[1:]
        return ("مُصحح (مقترح)", cand, 0.75)

    # إذا كان الجذر ثنائي ممدود بواو (دمو)
    if root.endswith("و") and len(root) == 3 and meanings == 0:
        cand = root[:2]
        return ("مُصحح (حذف واو زائدة)", cand, 0.80)

    # default: صحيح
    return ("صحيح", root, 0.70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", action="store_true", help="عرض الجدول للمراجعة")
    ns = parser.parse_args()

    if not VERIFY_DIR.exists():
        print(
            f"لا يوجد {VERIFY_DIR} — شغّل verify_roots_export.py أولاً", file=sys.stderr
        )
        return 1

    rows = []
    for path in sorted(VERIFY_DIR.glob("*.json")):
        if path.name == "index.json":
            continue
        info = json.loads(path.read_text(encoding="utf-8"))
        root = info["root_stored"]
        status, corrected, conf = classify(root, info)
        # مثال آية
        example = ""
        if info["ayat_sample"]:
            a = info["ayat_sample"][0]
            example = f"{a['surah']}:{a['ayah']} {a['word']}"
        rows.append(
            {
                "root_id": info["root_id"],
                "root_stored": root,
                "root_corrected": corrected,
                "status": status,
                "confidence": f"{conf:.2f}",
                "occurrences": info["quran_occurrences"],
                "meanings_current": info["meanings_count_current"],
                "starts_with_ya": info["starts_with_ya"],
                "arabic_match": info["arabic_roots_json_match"],
                "variants": ",".join(info["arabic_roots_variants_found"]),
                "example_ayah": example,
                "note": info["verification_hint"],
            }
        )

    # ترتيب: أولاً التي تبدأ بـ ى، ثم حسب occurrences تنازلياً
    rows.sort(key=lambda r: (0 if r["starts_with_ya"] else 1, -r["occurrences"]))

    # كتابة CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"كتب {len(rows)} صفاً إلى {OUT_CSV}")

    # تقرير markdown
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("# تقرير التحقق من الجذور (87)\n\n")
        f.write(
            "| الجذر | المصحح | الحالة | الثقة | التكرار | المعاني | مثال آية | ملاحظة |\n"
        )
        f.write(
            "|-------|--------|--------|-------|---------|---------|-----------|---------|\n"
        )
        for r in rows:
            f.write(
                f"| {r['root_stored']} | {r['root_corrected']} | {r['status']} | {r['confidence']} | {r['occurrences']} | {r['meanings_current']} | {r['example_ayah']} | {r['note']} |\n"
            )
        f.write("\n## الإحصاء\n")
        from collections import Counter

        cnt = Counter(r["status"] for r in rows)
        for k, v in cnt.items():
            f.write(f"- {k}: {v}\n")

    print(f"كتب التقرير إلى {OUT_REPORT}")

    if ns.review:
        # عرض ملخص
        from collections import Counter

        cnt = Counter(r["status"] for r in rows)
        print("\nالإحصاء:")
        for k, v in cnt.items():
            print(f"  {k}: {v}")
        print("\nأمثلة تحتاج مراجعة يدوية (ثقة <0.85):")
        for r in rows:
            if float(r["confidence"]) < 0.85:
                print(
                    f"  {r['root_stored']} → {r['root_corrected']} ({r['status']}, {r['confidence']}) ex: {r['example_ayah']}"
                )

    return 0


if __name__ == "__main__":
    sys.exit(main())
