#!/usr/bin/env python3
"""
Stage 2: enrich the Quran database with morphological analysis and Arabic
meanings, replacing the old heuristic root extraction.

Inputs (stage 1 + fetched data):
  data/quran_words.db                  - built by build_db.py
  data/quranic_corpus_morphology.json  - fetched by fetch_corpus.py
  data/arabic_roots.json               - fetched by fetch_arabic_roots.py

What it does:
  * Converts corpus Buckwalter roots/lemmas to Arabic.
  * Rebuilds the roots table with the verified corpus roots.
  * Populates word_morphology for every word occurrence (via location).
  * Populates lemmas and root_meanings (Arabic definitions from classical
    lexicons via the arabic-roots dataset).
  * Registers the new sources (Quranic Arabic Corpus, Arabic Lexicon).
  * Prints a coverage report.
"""

import json
import os
import sqlite3
import sys

BASE_DIR = "/home/ahmed/0/quran/quran-words"
DB_PATH = f"{BASE_DIR}/data/quran_words.db"
CORPUS_PATH = f"{BASE_DIR}/data/quranic_corpus_morphology.json"
ROOTS_PATH = f"{BASE_DIR}/data/arabic_roots.json"

# ---------------------------------------------------------------------------
# Buckwalter -> Arabic
# ---------------------------------------------------------------------------
BW_TO_AR = {
    "'": "ء",
    ">": "آ",
    "|": "آ",
    "&": "ٱ",
    "<": "إ",
    "}": "أ",
    "A": "ى",
    "b": "ب",
    "p": "ة",
    "t": "ت",
    "v": "ث",
    "j": "ج",
    "H": "ح",
    "x": "خ",
    "d": "د",
    "*": "ذ",
    "r": "ر",
    "z": "ز",
    "s": "س",
    "$": "ش",
    "S": "ص",
    "D": "ض",
    "T": "ط",
    "Z": "ظ",
    "E": "ع",
    "g": "غ",
    "f": "ف",
    "q": "ق",
    "k": "ك",
    "l": "ل",
    "m": "م",
    "n": "ن",
    "h": "ه",
    "w": "و",
    "y": "ي",
    "a": "َ",
    "u": "ُ",
    "i": "ِ",
    "~": "ّ",
    "o": "ً",
    "F": "ً",
    "N": "ٌ",
    "K": "ٍ",
    "^": "ْ",
    "`": "ٰ",
    "{": "ٱ",
}

ALEF_VARIANTS = str.maketrans({"آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا"})


def bw_to_ar(text):
    return "".join(BW_TO_AR.get(ch, ch) for ch in text)


def normalize_ar(text):
    """Canonical form used for matching with dictionary roots."""
    return text.translate(ALEF_VARIANTS).replace("ى", "ي")


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
SOURCES = [
    (
        "Quran.com API",
        "Quran word-by-word translation data (CC-BY-4.0)",
        "https://api.quran.com",
    ),
    (
        "Quranic Arabic Corpus v0.4",
        "Morphological annotation of every Quran word: root, lemma, part of speech and inflection features (GPL, Kais Dukes / University of Leeds)",
        "http://corpus.quran.com",
    ),
    (
        "Arabic Lexicon (Hawramani)",
        "Arabic root definitions from classical lexicons: مفردات غريب القرآن للراغب الأصفهاني، لسان العرب، تاج العروس، الصحاح، القاموس المحيط (GPL-3.0)",
        "http://arabiclexicon.hawramani.com",
    ),
]


def load_roots_lexicon():
    with open(ROOTS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    exact = {}
    normalized = {}
    for root, entries in raw.items():
        exact[root] = entries
        normalized.setdefault(normalize_ar(root), []).extend(entries)
    return exact, normalized


def main():
    print("=== المرحلة 2: التحليل الصرفي والمعاني العربية ===\n")

    if not os.path.exists(CORPUS_PATH) or not os.path.exists(ROOTS_PATH):
        sys.exit(
            "Missing data files - run fetch_corpus.py and fetch_arabic_roots.py first"
        )

    with open(CORPUS_PATH, encoding="utf-8") as f:
        corpus = json.load(f)
    print(f"Corpus tokens: {len(corpus)}")

    roots_exact, roots_norm = load_roots_lexicon()
    print(f"Arabic lexicon roots: {len(roots_exact)}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- register sources -------------------------------------------------
    c.execute("SELECT id, name FROM sources")
    existing = {name: sid for sid, name in c.fetchall()}
    source_ids = {}
    for name, desc, url in SOURCES:
        if name in existing:
            source_ids[name] = existing[name]
        else:
            c.execute(
                "INSERT INTO sources (name, description, url) VALUES (?, ?, ?)",
                (name, desc, url),
            )
            source_ids[name] = c.lastrowid
    corpus_source_id = source_ids["Quranic Arabic Corpus v0.4"]
    print(f"Sources: {source_ids}")

    # --- build location -> word_ayah map ----------------------------------
    c.execute("SELECT id, location FROM word_ayah")
    wa_by_loc = {}
    missing_loc = 0
    for wa_id, loc in c.fetchall():
        if loc:
            wa_by_loc[loc] = wa_id
        else:
            missing_loc += 1
    print(f"word_ayah rows: {len(wa_by_loc)} with location, {missing_loc} without")

    # --- collect roots & lemmas -------------------------------------------
    print("\nBuilding roots and lemmas...")
    root_ids = {}  # arabic root -> id
    lemma_ids = {}  # arabic lemma -> id
    c.execute("DELETE FROM roots")
    c.execute("DELETE FROM lemmas")

    for t in corpus:
        root_bw = t.get("root")
        if root_bw:
            root_ar = bw_to_ar(root_bw)
            if root_ar not in root_ids:
                c.execute("INSERT INTO roots (root) VALUES (?)", (root_ar,))
                root_ids[root_ar] = c.lastrowid
        lemma_bw = t.get("lemma")
        if lemma_bw:
            lemma_ar = bw_to_ar(lemma_bw)
            if lemma_ar not in lemma_ids:
                c.execute(
                    "INSERT INTO lemmas (lemma_ar, lemma_bw) VALUES (?, ?)",
                    (lemma_ar, lemma_bw),
                )
                lemma_ids[lemma_ar] = c.lastrowid
    print(f"Roots: {len(root_ids)}, Lemmas: {len(lemma_ids)}")

    # --- word_morphology --------------------------------------------------
    print("Inserting word_morphology...")
    c.execute("DELETE FROM word_morphology")
    n_matched = 0
    n_unmatched = 0
    unmatched_samples = []
    for t in corpus:
        wa_id = wa_by_loc.get(t["location"])
        if wa_id is None:
            n_unmatched += 1
            if len(unmatched_samples) < 5:
                unmatched_samples.append(t["location"])
            continue
        root_ar = bw_to_ar(t["root"]) if t.get("root") else None
        lemma_ar = bw_to_ar(t["lemma"]) if t.get("lemma") else None
        segments = json.dumps(t.get("segments", []), ensure_ascii=False)
        c.execute(
            """INSERT INTO word_morphology
                     (word_ayah_id, pos, form, aspect, mood, voice, person,
                      gender, number, grammatical_case, state, derivation, special,
                      root_id, lemma_id, segments)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                wa_id,
                t.get("pos"),
                t.get("form"),
                t.get("aspect"),
                t.get("mood"),
                t.get("voice"),
                t.get("person"),
                t.get("gender"),
                t.get("number"),
                t.get("grammatical_case"),
                t.get("state"),
                t.get("derivation"),
                bw_to_ar(t["special"]) if t.get("special") else None,
                root_ids.get(root_ar),
                lemma_ids.get(lemma_ar),
                segments,
            ),
        )
        n_matched += 1
    print(f"Morphology rows: {n_matched}, unmatched corpus tokens: {n_unmatched}")
    if unmatched_samples:
        print(f"  unmatched samples: {unmatched_samples}")

    # --- link words to the corpus source ----------------------------------
    c.execute(
        """INSERT OR IGNORE INTO word_sources (word_id, source_id)
                 SELECT DISTINCT wa.word_id, ?
                 FROM word_ayah wa
                 JOIN word_morphology wm ON wm.word_ayah_id = wa.id""",
        (corpus_source_id,),
    )

    # --- root meanings ----------------------------------------------------
    print("Inserting root_meanings...")
    c.execute("DELETE FROM root_meanings")
    n_with_meaning = 0
    n_without_meaning = 0
    for root_ar, root_id in root_ids.items():
        entries = roots_exact.get(root_ar) or roots_norm.get(normalize_ar(root_ar))
        if entries:
            n_with_meaning += 1
            for e in entries:
                c.execute(
                    "INSERT INTO root_meanings (root_id, definition, book_name, source_url) VALUES (?, ?, ?, ?)",
                    (root_id, e["definition"], e["book_name"], e["url"]),
                )
        else:
            n_without_meaning += 1
    print(f"Roots with Arabic meaning: {n_with_meaning}, without: {n_without_meaning}")

    conn.commit()
    verify(conn)
    conn.close()


def verify(conn):
    c = conn.cursor()
    print("\n=== التحقق من قاعدة البيانات (المرحلة 2) ===\n")

    for table in (
        "roots",
        "lemmas",
        "word_morphology",
        "root_meanings",
        "word_sources",
        "sources",
    ):
        c.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"سجلات {table}: {c.fetchone()[0]}")

    print("\n=== عينات ===\n")

    print("1) كلمات سورة الفاتحة مع التحليل الصرفي:")
    c.execute("""
        SELECT a.ayah, wa.position, w.text, wm.pos, wm.root_id IS NOT NULL as has_root,
               wm.form, wm.aspect, wm.gender, wm.number, wm.grammatical_case
        FROM word_ayah wa
        JOIN words w ON wa.word_id = w.id
        JOIN ayat a ON wa.ayah_id = a.id
        LEFT JOIN word_morphology wm ON wm.word_ayah_id = wa.id
        WHERE a.surah = 1
        ORDER BY a.ayah, wa.position
        LIMIT 14
    """)
    for row in c.fetchall():
        print(
            f"  {row[0]}:{row[1]} {row[2]} | pos={row[3]} root={row[4]} form={row[5]} aspect={row[6]} g={row[7]} n={row[8]} case={row[9]}"
        )

    print("\n2) جذر «كتب» ومعناه:")
    c.execute("""
        SELECT r.root, rm.book_name, substr(rm.definition, 1, 90)
        FROM roots r
        JOIN root_meanings rm ON rm.root_id = r.id
        WHERE r.root = 'كتب'
        LIMIT 5
    """)
    for row in c.fetchall():
        print(f"  {row[0]} [{row[1]}]: {row[2]}...")

    print("\n3) كلمة «ٱللَّهِ» (الجذر أله):")
    c.execute("""
        SELECT w.text, r.root, wm.pos
        FROM word_ayah wa
        JOIN words w ON wa.word_id = w.id
        JOIN word_morphology wm ON wm.word_ayah_id = wa.id
        JOIN roots r ON r.id = wm.root_id
        WHERE w.text = 'ٱللَّهِ'
        LIMIT 3
    """)
    for row in c.fetchall():
        print(f"  {row[0]} -> جذر {row[1]} (pos={row[2]})")

    print("\n4) أفعال ماضية مجهولة (PASS):")
    c.execute("""
        SELECT COUNT(*)
        FROM word_morphology
        WHERE aspect = 'PERF' AND voice = 'PASS'
    """)
    print(f"  {c.fetchone()[0]} موضعاً")

    print("\n5) تغطية الصرف:")
    c.execute("SELECT COUNT(*) FROM word_ayah")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM word_morphology")
    morphed = c.fetchone()[0]
    print(f"  {morphed}/{total} موضعاً ({100.0 * morphed / total:.2f}%)")


if __name__ == "__main__":
    main()
