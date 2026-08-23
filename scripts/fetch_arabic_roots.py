#!/usr/bin/env python3
"""
Download the Arabic roots lexicon dataset (MohamedRashad/arabic-roots, GPL-3.0)
from Hugging Face and convert it to a JSON index.

Dataset: https://huggingface.co/datasets/MohamedRashad/arabic-roots
  root       - Arabic root (e.g. كتب)
  definition - Arabic definition from a classical lexicon
  book_name  - lexicon name (e.g. مفردات غريب القرآن للراغب الأصفهاني)
  url        - source URL (arabiclexicon.hawramani.com)

Output: data/arabic_roots.json  { root: [ {definition, book_name, url}, ... ] }
"""

import json
import os
import subprocess
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARQUET_PATH = os.path.join(BASE_DIR, "data", "arabic_roots.parquet")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "arabic_roots.json")
PARQUET_URL = "https://huggingface.co/datasets/MohamedRashad/arabic-roots/resolve/main/data/train-00000-of-00001.parquet"

# Expected size from the HF API (bytes). Used only as a sanity hint.
EXPECTED_SIZE = 82_648_135


def download():
    if os.path.exists(PARQUET_PATH) and _looks_complete(PARQUET_PATH):
        print(f"Using existing file: {PARQUET_PATH}")
        return

    print(f"Downloading {PARQUET_URL}")
    # Use curl with resume support; fall back to wget.
    cmd = [
        "curl",
        "-sL",
        "--fail",
        "-C",
        "-",
        "--retry",
        "5",
        "--retry-delay",
        "3",
        "-o",
        PARQUET_PATH,
        PARQUET_URL,
    ]
    for _ in range(3):
        print("  running:", " ".join(cmd))
        code = subprocess.call(cmd)
        if code == 0 and _looks_complete(PARQUET_PATH):
            print(f"  downloaded {os.path.getsize(PARQUET_PATH)} bytes")
            return
        time.sleep(5)
    raise SystemExit("Failed to download arabic-roots parquet")


def _looks_complete(path):
    try:
        size = os.path.getsize(path)
        if size < 1_000_000:
            return False
        with open(path, "rb") as f:
            f.seek(size - 8)
            return f.read(4) == b"PAR1"
    except OSError:
        return False


def find_pyarrow_python():
    for py in (sys.executable, "python3.13", "python3.12", "python3.10"):
        try:
            code = subprocess.run(
                [py, "-c", "import pyarrow; print(pyarrow.__version__)"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if code.returncode == 0:
                return py
        except Exception:
            continue
    return None


def convert():
    py = find_pyarrow_python()
    if not py:
        raise SystemExit(
            "pyarrow not available in any python - install it: pip install pyarrow"
        )

    script = r"""
import json, sys
import pyarrow.parquet as pq
table = pq.read_table(sys.argv[1])
df = table.to_pandas()
roots = {}
for _, row in df.iterrows():
    root = str(row["root"]).strip()
    entry = {
        "definition": str(row["definition"]),
        "book_name": str(row["book_name"]),
        "url": str(row["url"]),
    }
    roots.setdefault(root, []).append(entry)
print(json.dumps(roots, ensure_ascii=False, indent=1))
"""
    print(f"Converting parquet with {py} ...")
    out = subprocess.run(
        [py, "-c", script, PARQUET_PATH], capture_output=True, text=True
    )
    if out.returncode != 0:
        print(out.stderr[-3000:], file=sys.stderr)
        raise SystemExit("Parquet conversion failed")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(out.stdout)
    data = json.loads(out.stdout)
    print(f"Saved {len(data)} roots -> {OUTPUT_PATH}")


def main():
    print("=== Fetching Arabic roots lexicon (arabic-roots) ===\n")
    download()
    convert()
    sample = json.load(open(OUTPUT_PATH, encoding="utf-8"))
    for r in ("كتب", "رحم", "أله"):
        if r in sample:
            print(f"  {r}: {sample[r][0]['book_name']}")
    books = set()
    for entries in sample.values():
        for e in entries:
            books.add(e["book_name"])
    print(f"\n{len(books)} lexicons:")
    for b in sorted(books):
        print("  -", b)


if __name__ == "__main__":
    main()
