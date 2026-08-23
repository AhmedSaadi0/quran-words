#!/usr/bin/env python3
"""Smoke-test the quran-words API against a running dev server.

Usage:
    python scripts/smoke_api.py --base http://127.0.0.1:8765/api
    python scripts/smoke_api.py --save /tmp/opencode/after   # save responses
    python scripts/smoke_api.py --compare /tmp/opencode/baseline  # diff vs saved
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

ENDPOINTS = {
    "stats": "/stats/",
    "search_ktb": "/search/?q=" + urllib.parse.quote("كتب"),
    "search_root_type": "/search/?q=" + urllib.parse.quote("رحم") + "&type=root",
    "roots_q": "/roots/?q=" + urllib.parse.quote("كتب"),
    "roots_p1": "/roots/?page=1",
    "masadir_ktb": "/masadir/?root=" + urllib.parse.quote("كتب"),
    "derivatives_ktb": "/derivatives/?root=" + urllib.parse.quote("كتب"),
    "derivatives_quranic": "/derivatives/?root="
    + urllib.parse.quote("كتب")
    + "&is_quranic=true",
    "meanings_ktb": "/meanings/?root=" + urllib.parse.quote("كتب"),
    "words_root": "/words/?root=" + urllib.parse.quote("كتب"),
    "word_29_detail": "/words/29/detail/",
    "word_ayah_ay1": "/word-ayah/?ayah=1",
    "surahs": "/surahs/",
    "ayah_words_s1": "/ayah-words/?surah=1",
    "ayat_s1": "/ayat/?surah=1",
}


def fetch(base: str, path: str):
    with urllib.request.urlopen(base.rstrip("/") + path, timeout=60) as r:
        return json.load(r)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000/api")
    parser.add_argument("--save", help="directory to save pretty JSON responses")
    parser.add_argument(
        "--compare", help="directory of saved responses to diff against"
    )
    args = parser.parse_args()

    import pathlib

    save_dir = pathlib.Path(args.save) if args.save else None
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)

    ok = fail = mismatch = 0
    for name, path in ENDPOINTS.items():
        try:
            data = fetch(args.base, path)
        except Exception as e:
            print(f"FAIL {name}: {e}")
            fail += 1
            continue

        if save_dir:
            (save_dir / f"{name}.json").write_text(
                json.dumps(data, ensure_ascii=False, sort_keys=True, indent=1),
                encoding="utf-8",
            )

        if args.compare:
            ref_file = pathlib.Path(args.compare) / f"{name}.json"
            if not ref_file.exists():
                print(f"DIFF {name}: no baseline file")
                mismatch += 1
                continue
            expected = json.loads(ref_file.read_text(encoding="utf-8"))
            if json.dumps(data, ensure_ascii=False, sort_keys=True) == json.dumps(
                expected, ensure_ascii=False, sort_keys=True
            ):
                print(f"OK   {name}")
                ok += 1
            else:
                print(f"DIFF {name}: response differs from baseline")
                mismatch += 1
        else:
            print(f"OK   {name}")
            ok += 1

    print(f"\n{ok} ok, {fail} failed, {mismatch} diff")
    return 1 if (fail or mismatch) else 0


if __name__ == "__main__":
    sys.exit(main())
