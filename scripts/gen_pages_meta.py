#!/usr/bin/env python3
"""
Generate frontend/src/lib/pages.generated.ts from DB true page boundaries.
Idempotent — reads data/quran_words.db ayat.page_number (Madina 604)
"""

from collections import defaultdict
import sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB = BASE / "data" / "quran_words.db"
OUT = BASE / "frontend" / "src" / "lib" / "pages.generated.ts"

conn = sqlite3.connect(DB)
cur = conn.execute(
    "SELECT page_number, surah, ayah FROM ayat ORDER BY page_number, surah, ayah"
)
pages: dict[int, list[tuple[int, int]]] = defaultdict(list)
for pn, s, a in cur.fetchall():
    pages[pn].append((s, a))
conn.close()

lines = []
lines.append(
    "// AUTO-GENERATED — do not edit. Generated from data/quran_words.db ayat.page_number (Madina 604)."
)
lines.append("// Source: scripts/gen_pages_meta.py / Quran.com API v4")
lines.append("export interface MushafPageBoundary {")
lines.append(
    "  page_number: number; start_surah: number; start_ayah: number; end_surah: number; end_ayah: number; ayah_count: number;"
)
lines.append("}")
lines.append("export const MUSH_PAGE_BOUNDARIES: MushafPageBoundary[] = [")
for pn in sorted(pages):
    lst = pages[pn]
    s_s, a_s = lst[0]
    s_e, a_e = lst[-1]
    lines.append(
        f"  {{ page_number: {pn}, start_surah: {s_s}, start_ayah: {a_s}, end_surah: {s_e}, end_ayah: {a_e}, ayah_count: {len(lst)} }},"
    )
lines.append("];")
lines.append(
    "export const MUSH_PAGE_MAP: Record<number, MushafPageBoundary> = Object.fromEntries(MUSH_PAGE_BOUNDARIES.map(p => [p.page_number, p]));"
)
surah_pages: dict[int, list[int]] = defaultdict(list)
for pn, lst in pages.items():
    for s, a in lst:
        if pn not in surah_pages[s]:
            surah_pages[s].append(pn)
lines.append("export const SURAH_PAGES: Record<number, number[]> = {")
for sid in sorted(surah_pages):
    lines.append(f"  {sid}: [{','.join(map(str, surah_pages[sid]))}],")
lines.append("};")
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT} — {len(pages)} pages")
