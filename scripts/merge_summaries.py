#!/usr/bin/env python3
"""
دمج نتائج تلخيص الوكلاء في data/root_ai_summary.json ثم إعادة بناء الطابور
Stage: Merge agent summary batches into the master JSON.

يقرأ كل ملفات /tmp/opencode/summary_results/*.json، ويدمج الجذور الجديدة فقط
(الموجود مسبقاً لا يُلمس)، ويحذف الملفات المدمجة، ثم يستدعي build_summary_queue.py.

الاستعمال:
  python scripts/merge_summaries.py [--results-dir /tmp/opencode/summary_results]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_JSON = ROOT / "data" / "root_ai_summary.json"
# لا يُستخدم كنص جاهز — الموديل نفسه يكتب اسمه في ملف النتائج.
# يُستخدم فقط كاحتياط عند قراءة دفعات قديمة بصيغة {"root": "summary string"}.
FALLBACK_MODEL = "muse-spark-1.2-contributor-free"


def _fallback_model() -> str:
    """يحاول معرفة الموديل الحالي ديناميكياً قبل السقوط على القيمة الافتراضية."""
    import os

    for key in ("OPENCODE_MODEL", "MODEL", "LLM_MODEL"):
        if os.environ.get(key):
            return os.environ[key].strip()
    p = ROOT / "data" / "current_model.txt"
    if p.exists():
        try:
            txt = p.read_text(encoding="utf-8").strip()
            if txt:
                return txt
        except Exception:
            pass
    return FALLBACK_MODEL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--results-dir", type=Path, default=Path("/tmp/opencode/summary_results")
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="استبدال الجذور الموجودة بدل تخطيها (لتجديد النسخ القديمة)",
    )
    ns = parser.parse_args()

    master = {}
    if SUMMARY_JSON.exists():
        master = json.loads(SUMMARY_JSON.read_text())

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added, skipped_files = 0, []
    if ns.results_dir.exists():
        for f in sorted(ns.results_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
            except json.JSONDecodeError as e:
                print(f"[skip] {f.name}: JSON غير صالح ({e})")
                continue
            if ns.replace:
                new_roots = dict(data)
            else:
                # JSON الآن يحوي كل الجذور بـ summary_ar=null للمُعلّق؛
                # ندمج فقط الجذور المعلقة (null) أو غير الموجودة
                new_roots = {}
                for k, v in data.items():
                    entry = master.get(k)
                    is_pending = (
                        entry is None
                        or (isinstance(entry, dict) and not entry.get("summary_ar"))
                        or (isinstance(entry, str) and not entry.strip())
                    )
                    if is_pending or k not in master:
                        new_roots[k] = v
            if not new_roots:
                # كل جذور هذا الملف مُنجزة مسبقاً — نحذف الملف كـ duplicate
                skipped_files.append(f)
                continue
            print(f"[merge] {f.name}: +{len(new_roots)} جذر")
            normalized = {}
            for k, v in new_roots.items():
                if isinstance(v, dict) and "summary_ar" in v:
                    # الوكيل كتب الموديل بنفسه — نحترمه
                    summary = v.get("summary_ar")
                    model = v.get("model") or _fallback_model()
                    gen = v.get("generated_at") or now
                else:
                    # صيغة قديمة: {"root": "summary string"}
                    summary = v if isinstance(v, str) else str(v)
                    model = _fallback_model()
                    gen = now
                if not summary or not str(summary).strip():
                    continue
                normalized[k] = {
                    "summary_ar": str(summary).strip(),
                    "model": model,
                    "generated_at": gen,
                }
            if not normalized:
                skipped_files.append(f)
                continue
            master.update(normalized)
            added += len(normalized)
            skipped_files.append(f)

    if ns.dry_run:
        print(f"dry-run: سيُضاف {added} جذر، الإجمالي بعد الدمج {len(master)}")
        return 0

    SUMMARY_JSON.write_text(json.dumps(master, ensure_ascii=False, indent=2) + "\n")
    for f in skipped_files:
        f.unlink()
    print(f"merged: +{added} جذر -> الإجمالي {len(master)} في {SUMMARY_JSON}")

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_summary_queue.py")])
    return 0


if __name__ == "__main__":
    sys.exit(main())
