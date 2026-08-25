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
MODEL = "ox-alpha"


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
                new_roots = {k: v for k, v in data.items() if k not in master}
            covered = set(data) <= set(master) or ns.replace
            if not new_roots:
                skipped_files.append(f)
                continue
            print(f"[merge] {f.name}: +{len(new_roots)} جذر")
            master.update(
                {
                    k: {"summary_ar": v, "model": MODEL, "generated_at": now}
                    for k, v in new_roots.items()
                }
            )
            added += len(new_roots)
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
