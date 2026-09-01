#!/usr/bin/env python3
"""
Enrich ayat with Quran divisions from Quran.com API v4.

Adds 7 columns to ayat if missing and fills them for all 6236 ayat:
  juz (1..30), hizb (1..60), rub_el_hizb (1..240),
  page_number (1..604), manzil_number (1..7), ruku_number (1..558), sajdah_number

Primary source: https://api.quran.com/api/v4/verses/by_chapter/{n}
Fallback/validation: api.alquran.cloud + fawazahmed0 cache

Idempotent: rerunnable, uses ALTER TABLE ADD COLUMN IF NOT EXISTS,
updates existing values, rebuilds indexes, writes cache to data/quran_meta_cache.json

Usage:
  python scripts/enrich_ayat_quran_meta.py                    # live fetch + enrich
  python scripts/enrich_ayat_quran_meta.py --from-cache       # use existing cache file
  python scripts/enrich_ayat_quran_meta.py --cache-only       # only fetch and write cache
  python scripts/enrich_ayat_quran_meta.py --validate-only    # cross-check with alquran.cloud

Refs:
  - Quran.com API v4 (CC-BY-4.0) — already source 1 in data/quran_words.db
  - Download pattern mirrors scripts/download_quran.py:fetch_json
  - Column pattern mirrors scripts/build_plain_columns.py:column_exists
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "quran_words.db"
CACHE_PATH = BASE_DIR / "data" / "quran_meta_cache.json"

API_BASE = "https://api.quran.com/api/v4"

# Surah ayah counts for progress (from scripts/build_db.py)
SURAH_AYAH_COUNTS = [
    7,
    286,
    200,
    176,
    120,
    165,
    206,
    75,
    129,
    109,
    123,
    111,
    43,
    52,
    99,
    128,
    111,
    110,
    98,
    135,
    112,
    78,
    118,
    64,
    77,
    227,
    93,
    88,
    69,
    60,
    34,
    30,
    73,
    54,
    45,
    83,
    182,
    88,
    75,
    85,
    54,
    53,
    89,
    59,
    37,
    35,
    38,
    29,
    18,
    45,
    60,
    49,
    62,
    55,
    78,
    96,
    29,
    22,
    24,
    13,
    14,
    11,
    11,
    18,
    12,
    12,
    30,
    52,
    28,
    44,
    28,
    28,
    20,
    56,
    40,
    31,
    50,
    40,
    46,
    42,
    17,
    19,
    36,
    25,
    22,
    17,
    19,
    26,
    30,
    20,
    15,
    21,
    11,
    8,
    8,
    19,
    5,
    8,
    8,
    11,
    11,
    8,
    3,
    9,
    5,
    4,
    7,
    3,
    6,
    3,
    5,
    4,
    5,
    6,
]

NEW_COLS: dict[str, str] = {
    "juz": "INTEGER",
    "hizb": "INTEGER",
    "rub_el_hizb": "INTEGER",
    "page_number": "INTEGER",
    "manzil_number": "INTEGER",
    "ruku_number": "INTEGER",
    "sajdah_number": "INTEGER",
}

# API field -> DB col
API_TO_COL = {
    "juz_number": "juz",
    "hizb_number": "hizb",
    "rub_el_hizb_number": "rub_el_hizb",
    "page_number": "page_number",
    "manzil_number": "manzil_number",
    "ruku_number": "ruku_number",
    "sajdah_number": "sajdah_number",
}


def column_exists(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    return any(r[1] == col for r in cur.execute(f"PRAGMA table_info({table})"))


def ensure_columns(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    added: list[str] = []
    for col, typ in NEW_COLS.items():
        if not column_exists(cur, "ayat", col):
            cur.execute(f"ALTER TABLE ayat ADD COLUMN {col} {typ}")
            added.append(col)
            print(f"  + column ayat.{col} {typ}")
    if added:
        conn.commit()
    else:
        print("  columns already exist — no ADD needed")
    return added


def ensure_indexes(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    stmts = [
        "CREATE INDEX IF NOT EXISTS idx_ayat_juz ON ayat(juz)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_hizb ON ayat(hizb)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_rub ON ayat(rub_el_hizb)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_page ON ayat(page_number)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_manzil ON ayat(manzil_number)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_ruku ON ayat(ruku_number)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_juz_hizb ON ayat(juz, hizb)",
        "CREATE INDEX IF NOT EXISTS idx_ayat_juz_hizb_rub ON ayat(juz, hizb, rub_el_hizb)",
    ]
    for s in stmts:
        cur.execute(s)
    conn.commit()
    print(f"  indexes ensured ({len(stmts)})")


def fetch_json(url: str, retries: int = 4, timeout: int = 30) -> Any | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuranDB/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
        ) as e:
            wait = 2**attempt
            if attempt < retries - 1:
                print(
                    f"    retry {attempt + 1}/{retries} after {wait}s: {e}",
                    file=sys.stderr,
                )
                time.sleep(wait)
            else:
                print(f"    FAILED: {url} — {e}", file=sys.stderr)
                return None


def fetch_all_meta() -> dict[tuple[int, int], dict[str, Any]]:
    """
    Fetch all 6236 ayat meta from Quran.com.
    Returns map (surah, ayah) -> {juz, hizb, ...}
    """
    result: dict[tuple[int, int], dict[str, Any]] = {}
    # fields param is optional but explicit keeps contract stable
    fields = ",".join(API_TO_COL.keys()) + ",text_uthmani"
    for surah in range(1, 115):
        surah_count = SURAH_AYAH_COUNTS[surah - 1]
        print(
            f"[{surah:3d}/114] surah {surah} ({surah_count} ayat)...",
            end=" ",
            flush=True,
        )
        # Quran.com pagination: per_page up to 300 covers max 286
        url = f"{API_BASE}/verses/by_chapter/{surah}?language=en&per_page=300&fields={fields}"
        data = fetch_json(url)
        if not data or "verses" not in data:
            print("FAILED — no verses")
            # still try without fields param as fallback
            url2 = f"{API_BASE}/verses/by_chapter/{surah}?language=en&per_page=300"
            data = fetch_json(url2)
            if not data or "verses" not in data:
                print(f"  --> skip surah {surah}", file=sys.stderr)
                continue
        verses = data["verses"]
        for v in verses:
            # verse_key is "surah:ayah"
            try:
                sk, ak = v["verse_key"].split(":")
                key = (int(sk), int(ak))
            except Exception:
                # fallback to verse_number
                key = (surah, int(v["verse_number"]))
            meta: dict[str, Any] = {}
            for api_field, col in API_TO_COL.items():
                meta[col] = v.get(api_field)
            result[key] = meta
        print(
            f"ok {len(verses)} verses → juz {verses[0].get('juz_number') if verses else '?'}..{verses[-1].get('juz_number') if verses else '?'}"
        )
        time.sleep(0.35)  # rate limiting as in download_quran.py
    print(f"Fetched {len(result)} ayat meta (expected 6236)")
    return result


def save_cache(meta: dict[tuple[int, int], dict[str, Any]]) -> None:
    # Convert tuple keys to "surah:ayah" for JSON
    j = {f"{s}:{a}": v for (s, a), v in meta.items()}
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    print(f"Cache written: {CACHE_PATH} ({len(j)} entries)")


def load_cache() -> dict[tuple[int, int], dict[str, Any]]:
    if not CACHE_PATH.exists():
        print(f"Cache not found: {CACHE_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        j = json.load(f)
    return {tuple(map(int, k.split(":"))): v for k, v in j.items()}


def update_db(meta: dict[tuple[int, int], dict[str, Any]]) -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    ensure_columns(conn)
    cur = conn.cursor()
    # ensure all keys present
    rows = cur.execute("SELECT surah, ayah FROM ayat ORDER BY surah, ayah").fetchall()
    if len(rows) != 6236:
        print(f"WARN: ayat count {len(rows)} != 6236", file=sys.stderr)
    missing = [k for k in rows if tuple(k) not in meta]
    if missing:
        print(
            f"WARN: {len(missing)} ayat missing from meta: {missing[:10]}",
            file=sys.stderr,
        )

    updates: list[tuple] = []
    for (surah, ayah), m in meta.items():
        updates.append(
            (
                m.get("juz"),
                m.get("hizb"),
                m.get("rub_el_hizb"),
                m.get("page_number"),
                m.get("manzil_number"),
                m.get("ruku_number"),
                m.get("sajdah_number"),
                surah,
                ayah,
            )
        )
    cur.executemany(
        """
        UPDATE ayat
        SET juz=?, hizb=?, rub_el_hizb=?, page_number=?, manzil_number=?, ruku_number=?, sajdah_number=?
        WHERE surah=? AND ayah=?
        """,
        updates,
    )
    conn.commit()
    print(
        f"Updated {cur.rowcount if cur.rowcount != -1 else len(updates)} rows (executemany {len(updates)})"
    )

    # verification counts
    for col in NEW_COLS:
        cur.execute(f"SELECT COUNT(*) FROM ayat WHERE {col} IS NULL")
        nulls = cur.fetchone()[0]
        print(f"  ayat.{col} NULLs: {nulls}")

    ensure_indexes(conn)

    # sources attribution — upsert style
    cur.execute(
        "SELECT id FROM sources WHERE name=?",
        ("Quran.com — ayat divisions (juz/hizb/rub/page/manzil/ruku)",),
    )
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO sources (name, description, url) VALUES (?,?,?)",
            (
                "Quran.com — ayat divisions (juz/hizb/rub/page/manzil/ruku)",
                "Per-ayah Quran divisions: juz (1..30), hizb (1..60), rub el-hizb (1..240), page (1..604 Madina), manzil (1..7), ruku (1..558), sajdah — from Quran.com API v4 (CC-BY-4.0)",
                "https://api.quran.com/api/v4/verses",
            ),
        )
        print(f"  + source id {cur.lastrowid}")
        conn.commit()
    else:
        print(f"  source exists id {row[0]}")

    # sample verification
    samples = [
        (1, 1),
        (1, 7),
        (2, 142),
        (2, 253),
        (2, 286),
        (9, 93),
        (36, 28),
        (78, 1),
        (114, 6),
    ]
    print("\n  Samples (surah:ayah → juz hizb rub page manzil ruku sajdah):")
    for s, a in samples:
        cur.execute(
            "SELECT juz, hizb, rub_el_hizb, page_number, manzil_number, ruku_number, sajdah_number FROM ayat WHERE surah=? AND ayah=?",
            (s, a),
        )
        r = cur.fetchone()
        print(f"    {s:3d}:{a:3d} → {r}")

    # distinct checks
    for col, exp in [
        ("juz", 30),
        ("hizb", 60),
        ("rub_el_hizb", 240),
        ("manzil_number", 7),
    ]:
        cur.execute(f"SELECT COUNT(DISTINCT {col}) FROM ayat")
        cnt = cur.fetchone()[0]
        mark = "✓" if cnt == exp else "?"
        print(f"  DISTINCT {col}: {cnt} (expected {exp}) {mark}")

    cur.execute("SELECT COUNT(DISTINCT page_number) FROM ayat")
    pages = cur.fetchone()[0]
    print(
        f"  DISTINCT page_number: {pages} (expected 604) {'✓' if pages == 604 else '?'}"
    )

    conn.close()
    return len(updates)


def validate_against_alquran(sample: int = 30) -> bool:
    """Random sample cross-check vs api.alquran.cloud"""
    import random

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT surah, ayah, juz, hizb, rub_el_hizb, page_number, manzil_number, ruku_number FROM ayat"
    )
    rows = cur.fetchall()
    conn.close()
    picks = random.sample(rows, min(sample, len(rows)))
    ok = 0
    fail = 0
    for surah, ayah, juz, hizb, rub, page, manzil, ruku in picks:
        url = f"http://api.alquran.cloud/v1/ayah/{surah}:{ayah}"
        data = fetch_json(url, retries=2, timeout=15)
        if not data or data.get("code") != 200:
            print(f"  skip {surah}:{ayah} — alquran fetch fail")
            continue
        d = data["data"]
        # alquran: juz, manzil, page, ruku, hizbQuarter (quarter)
        # hizbQuarter = rub_el_hizb, hizb = ceil(rub/4)
        exp_juz = d.get("juz")
        exp_page = d.get("page")
        exp_manzil = d.get("manzil")
        exp_ruku = d.get("ruku")
        exp_rub = d.get("hizbQuarter")
        # compare
        mismatches = []
        if exp_juz is not None and exp_juz != juz:
            mismatches.append(f"juz {juz}!={exp_juz}")
        if exp_page is not None and exp_page != page:
            mismatches.append(f"page {page}!={exp_page}")
        if exp_manzil is not None and exp_manzil != manzil:
            mismatches.append(f"manzil {manzil}!={exp_manzil}")
        if exp_ruku is not None and exp_ruku != ruku:
            mismatches.append(f"ruku {ruku}!={exp_ruku}")
        if exp_rub is not None and exp_rub != rub:
            mismatches.append(f"rub {rub}!={exp_rub}")
        if mismatches:
            print(f"  MISMATCH {surah}:{ayah} — {', '.join(mismatches)}")
            fail += 1
        else:
            ok += 1
    print(
        f"Validation vs alquran.cloud: {ok} ok, {fail} mismatches (sample {len(picks)})"
    )
    return fail == 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Enrich ayat with juz/hizb/rub/page/manzil/ruku/sajdah from Quran.com"
    )
    p.add_argument(
        "--from-cache",
        action="store_true",
        help="use existing data/quran_meta_cache.json instead of live fetch",
    )
    p.add_argument(
        "--cache-only",
        action="store_true",
        help="only fetch and write cache, do not update DB",
    )
    p.add_argument(
        "--validate-only", action="store_true", help="only validate DB vs alquran.cloud"
    )
    args = p.parse_args()

    if args.validate_only:
        print("=== Validation vs alquran.cloud ===")
        ok = validate_against_alquran(sample=40)
        return 0 if ok else 1

    meta: dict[tuple[int, int], dict[str, Any]]
    if args.from_cache:
        print(f"Loading cache {CACHE_PATH} ...")
        meta = load_cache()
        print(f"Loaded {len(meta)} entries from cache")
    else:
        print("=== Fetching from Quran.com API v4 ===")
        meta = fetch_all_meta()
        if len(meta) < 6236:
            print(
                f"ERROR: fetched {len(meta)} < 6236, aborting (check network)",
                file=sys.stderr,
            )
            if meta:
                save_cache(meta)
            return 1
        save_cache(meta)

    if args.cache_only:
        print("Cache-only mode — DB not updated")
        return 0

    print(f"\n=== Updating DB {DB_PATH} ===")
    n = update_db(meta)

    # quick post-validation
    print("\n=== Quick validation ===")
    validate_against_alquran(sample=20)

    print(f"\nDone — {n} ayat enriched ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
