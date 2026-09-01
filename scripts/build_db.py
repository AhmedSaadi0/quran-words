#!/usr/bin/env python3
"""
Create the base Quran Words SQLite database with proper relational structure.

Stage 1 of the pipeline: builds surahs, ayat, words, word_ayah from the
Quran.com word-by-word JSON. Morphological analysis and Arabic meanings are
added in stage 2 by scripts/build_morphology.py.

Tables (stage 1): surahs, ayat, words, word_ayah, sources
Tables (stage 2, by build_morphology.py): roots, lemmas, word_morphology,
root_meanings, word_sources
"""

import json
import re
import sqlite3

BASE_DIR = "/home/ahmed/0/quran/quran-words"
DB_PATH = f"{BASE_DIR}/data/quran_words.db"
DATA_PATH = "/home/ahmed/0/quran/quran_words_wbw.json"

# Surah info: (name_ar, name_en, ayah_count, revelation_type, juz_start)
SURAH_INFO = [
    ("الفاتحة", "Al-Fatiha", 7, "مكية", 1),
    ("البقرة", "Al-Baqarah", 286, "مدنية", 1),
    ("آل عمران", "Aal-E-Imran", 200, "مدنية", 3),
    ("النساء", "An-Nisa", 176, "مدنية", 4),
    ("المائدة", "Al-Ma'idah", 120, "مدنية", 6),
    ("الأنعام", "Al-An'am", 165, "مكية", 7),
    ("الأعراف", "Al-A'raf", 206, "مكية", 8),
    ("الأنفال", "Al-Anfal", 75, "مدنية", 10),
    ("التوبة", "At-Tawbah", 129, "مدنية", 10),
    ("يونس", "Yunus", 109, "مكية", 11),
    ("هود", "Hud", 123, "مكية", 11),
    ("يوسف", "Yusuf", 111, "مكية", 12),
    ("الرعد", "Ar-Ra'd", 43, "مدنية", 13),
    ("إبراهيم", "Ibrahim", 52, "مكية", 13),
    ("الحجر", "Al-Hijr", 99, "مكية", 14),
    ("النحل", "An-Nahl", 128, "مكية", 14),
    ("الإسراء", "Al-Isra", 111, "مكية", 15),
    ("الكهف", "Al-Kahf", 110, "مكية", 15),
    ("مريم", "Maryam", 98, "مكية", 16),
    ("طه", "Taha", 135, "مكية", 16),
    ("الأنبياء", "Al-Anbiya", 112, "مكية", 17),
    ("الحج", "Al-Hajj", 78, "مدنية", 17),
    ("المؤمنون", "Al-Mu'minun", 118, "مكية", 18),
    ("النور", "An-Nur", 64, "مدنية", 18),
    ("الفرقان", "Al-Furqan", 77, "مكية", 18),
    ("الشعراء", "Ash-Shu'ara", 227, "مكية", 19),
    ("النمل", "An-Naml", 93, "مكية", 20),
    ("القصص", "Al-Qasas", 88, "مكية", 20),
    ("العنكبوت", "Al-Ankabut", 69, "مكية", 20),
    ("الروم", "Ar-Rum", 60, "مكية", 21),
    ("لقمان", "Luqman", 34, "مكية", 21),
    ("السجدة", "As-Sajdah", 30, "مكية", 21),
    ("الأحزاب", "Al-Ahzab", 73, "مدنية", 21),
    ("سبأ", "Saba", 54, "مكية", 22),
    ("فاطر", "Fatir", 45, "مكية", 22),
    ("يس", "Ya-Sin", 83, "مكية", 22),
    ("الصافات", "As-Saffat", 182, "مكية", 23),
    ("ص", "Sad", 88, "مكية", 23),
    ("الزمر", "Az-Zumar", 75, "مكية", 23),
    ("غافر", "Ghafir", 85, "مكية", 24),
    ("فصلت", "Fussilat", 54, "مكية", 24),
    ("الشورى", "Ash-Shura", 53, "مكية", 25),
    ("الزخرف", "Az-Zukhruf", 89, "مكية", 25),
    ("الدخان", "Ad-Dukhan", 59, "مكية", 25),
    ("الجاثية", "Al-Jathiyah", 37, "مكية", 25),
    ("الأحقاف", "Al-Ahqaf", 35, "مكية", 26),
    ("محمد", "Muhammad", 38, "مدنية", 26),
    ("الفتح", "Al-Fath", 29, "مدنية", 26),
    ("الحجرات", "Al-Hujurat", 18, "مدنية", 26),
    ("ق", "Qaf", 45, "مكية", 26),
    ("الذاريات", "Adh-Dhariyat", 60, "مكية", 26),
    ("الطور", "At-Tur", 49, "مكية", 27),
    ("النجم", "An-Najm", 62, "مكية", 27),
    ("القمر", "Al-Qamar", 55, "مكية", 27),
    ("الرحمن", "Ar-Rahman", 78, "مدنية", 27),
    ("الواقعة", "Al-Waqi'ah", 96, "مكية", 27),
    ("الحديد", "Al-Hadid", 29, "مدنية", 27),
    ("المجادلة", "Al-Mujadilah", 22, "مدنية", 28),
    ("الحشر", "Al-Hashr", 24, "مدنية", 28),
    ("الممتحنة", "Al-Mumtahanah", 13, "مدنية", 28),
    ("الصف", "As-Saff", 14, "مدنية", 28),
    ("الجمعة", "Al-Jumu'ah", 11, "مدنية", 28),
    ("المنافقون", "Al-Munafiqun", 11, "مدنية", 28),
    ("التغابن", "At-Taghabun", 18, "مدنية", 28),
    ("الطلاق", "At-Talaq", 12, "مدنية", 28),
    ("التحريم", "At-Tahrim", 12, "مدنية", 28),
    ("الملك", "Al-Mulk", 30, "مكية", 29),
    ("القلم", "Al-Qalam", 52, "مكية", 29),
    ("الحاقة", "Al-Haqqah", 52, "مكية", 29),
    ("المعارج", "Al-Ma'arij", 44, "مكية", 29),
    ("نوح", "Nuh", 28, "مكية", 29),
    ("الجن", "Al-Jinn", 28, "مكية", 29),
    ("المزمل", "Al-Muzzammil", 20, "مكية", 29),
    ("المدثر", "Al-Muddaththir", 56, "مكية", 29),
    ("القيامة", "Al-Qiyamah", 40, "مكية", 29),
    ("الإنسان", "Al-Insan", 31, "مدنية", 29),
    ("المرسلات", "Al-Mursalat", 50, "مكية", 29),
    ("النبأ", "An-Naba", 40, "مكية", 30),
    ("النازعات", "An-Nazi'at", 46, "مكية", 30),
    ("عبس", "Abasa", 42, "مكية", 30),
    ("التكوير", "At-Takwir", 29, "مكية", 30),
    ("الانفطار", "Al-Infitar", 19, "مكية", 30),
    ("المطففين", "Al-Mutaffifin", 36, "مكية", 30),
    ("الانشقاق", "Al-Inshiqaq", 25, "مكية", 30),
    ("البروج", "Al-Buruj", 22, "مكية", 30),
    ("الطارق", "At-Tariq", 17, "مكية", 30),
    ("الأعلى", "Al-A'la", 19, "مكية", 30),
    ("الغاشية", "Al-Ghashiyah", 26, "مكية", 30),
    ("الفجر", "Al-Fajr", 30, "مكية", 30),
    ("البلد", "Al-Balad", 20, "مكية", 30),
    ("الشمس", "Ash-Shams", 15, "مكية", 30),
    ("الليل", "Al-Layl", 21, "مكية", 30),
    ("الضحى", "Ad-Duha", 11, "مكية", 30),
    ("الشرح", "Ash-Sharh", 8, "مكية", 30),
    ("التين", "At-Tin", 8, "مكية", 30),
    ("العلق", "Al-Alaq", 19, "مكية", 30),
    ("القدر", "Al-Qadr", 5, "مكية", 30),
    ("البينة", "Al-Bayyinah", 8, "مدنية", 30),
    ("الزلزلة", "Az-Zalzalah", 8, "مدنية", 30),
    ("العاديات", "Al-Adiyat", 11, "مكية", 30),
    ("القارعة", "Al-Qari'ah", 11, "مكية", 30),
    ("التكاثر", "At-Takathur", 8, "مكية", 30),
    ("العصر", "Al-Asr", 3, "مكية", 30),
    ("الهمزة", "Al-Humazah", 9, "مكية", 30),
    ("الفيل", "Al-Fil", 5, "مكية", 30),
    ("قريش", "Quraysh", 4, "مكية", 30),
    ("الماعون", "Al-Ma'un", 7, "مكية", 30),
    ("الكوثر", "Al-Kawthar", 3, "مكية", 30),
    ("الكافرون", "Al-Kafirun", 6, "مكية", 30),
    ("النصر", "An-Nasr", 3, "مدنية", 30),
    ("المسد", "Al-Masad", 5, "مكية", 30),
    ("الإخلاص", "Al-Ikhlas", 4, "مكية", 30),
    ("الفلق", "Al-Falaq", 5, "مكية", 30),
    ("الناس", "An-Nas", 6, "مكية", 30),
]


def strip_diacritics(text):
    """Remove Arabic diacritics (tashkeel) from text."""
    diacritics = re.compile(
        r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed]"
    )
    return diacritics.sub("", text)


def create_database():
    """Create the SQLite database with all tables (stage 1)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in c.fetchall()]
    for table in tables:
        c.execute(f"DROP TABLE IF EXISTS {table}")

    c.execute("""CREATE TABLE surahs (
        id INTEGER PRIMARY KEY,
        name_ar TEXT NOT NULL,
        name_en TEXT NOT NULL,
        ayah_count INTEGER NOT NULL,
        revelation_type TEXT NOT NULL,
        juz_start INTEGER NOT NULL
    )""")

    c.execute("""CREATE TABLE ayat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        surah INTEGER NOT NULL,
        ayah INTEGER NOT NULL,
        text_uthmani TEXT,
        text_imlaei TEXT,
        word_count INTEGER,
        juz INTEGER,
        hizb INTEGER,
        rub_el_hizb INTEGER,
        page_number INTEGER,
        manzil_number INTEGER,
        ruku_number INTEGER,
        sajdah_number INTEGER,
        FOREIGN KEY (surah) REFERENCES surahs(id),
        UNIQUE(surah, ayah)
    )""")

    c.execute("""CREATE TABLE words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        text_clean TEXT,
        translation TEXT,
        transliteration TEXT,
        position_in_ayah INTEGER
    )""")

    c.execute("""CREATE TABLE word_ayah (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        ayah_id INTEGER NOT NULL,
        position INTEGER NOT NULL,
        location TEXT,
        FOREIGN KEY (word_id) REFERENCES words(id),
        FOREIGN KEY (ayah_id) REFERENCES ayat(id),
        UNIQUE(word_id, ayah_id, position)
    )""")

    c.execute("""CREATE TABLE sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        url TEXT
    )""")

    c.execute("""CREATE TABLE roots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        root TEXT NOT NULL UNIQUE
    )""")

    c.execute("""CREATE TABLE lemmas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lemma_ar TEXT UNIQUE,
        lemma_bw TEXT
    )""")

    c.execute("""CREATE TABLE word_morphology (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_ayah_id INTEGER NOT NULL UNIQUE,
        pos TEXT,
        form TEXT,
        aspect TEXT,
        mood TEXT,
        voice TEXT,
        person TEXT,
        gender TEXT,
        number TEXT,
        grammatical_case TEXT,
        state TEXT,
        derivation TEXT,
        special TEXT,
        root_id INTEGER,
        lemma_id INTEGER,
        segments TEXT,
        FOREIGN KEY (word_ayah_id) REFERENCES word_ayah(id),
        FOREIGN KEY (root_id) REFERENCES roots(id),
        FOREIGN KEY (lemma_id) REFERENCES lemmas(id)
    )""")

    c.execute("""CREATE TABLE root_meanings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        root_id INTEGER NOT NULL,
        definition TEXT,
        book_name TEXT,
        source_url TEXT,
        FOREIGN KEY (root_id) REFERENCES roots(id)
    )""")

    c.execute("""CREATE TABLE word_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL,
        FOREIGN KEY (word_id) REFERENCES words(id),
        FOREIGN KEY (source_id) REFERENCES sources(id),
        UNIQUE(word_id, source_id)
    )""")

    c.execute("CREATE INDEX idx_words_text ON words(text)")
    c.execute("CREATE INDEX idx_words_text_clean ON words(text_clean)")
    c.execute("CREATE INDEX idx_words_translation ON words(translation)")
    c.execute("CREATE INDEX idx_ayat_surah ON ayat(surah)")
    c.execute("CREATE INDEX idx_ayat_surah_ayah ON ayat(surah, ayah)")
    c.execute("CREATE INDEX idx_ayat_juz ON ayat(juz)")
    c.execute("CREATE INDEX idx_ayat_hizb ON ayat(hizb)")
    c.execute("CREATE INDEX idx_ayat_rub ON ayat(rub_el_hizb)")
    c.execute("CREATE INDEX idx_ayat_page ON ayat(page_number)")
    c.execute("CREATE INDEX idx_ayat_juz_hizb ON ayat(juz, hizb)")
    c.execute("CREATE INDEX idx_ayat_juz_hizb_rub ON ayat(juz, hizb, rub_el_hizb)")
    c.execute("CREATE INDEX idx_word_ayah_word ON word_ayah(word_id)")
    c.execute("CREATE INDEX idx_word_ayah_ayah ON word_ayah(ayah_id)")
    c.execute("CREATE INDEX idx_word_ayah_location ON word_ayah(location)")
    c.execute("CREATE INDEX idx_roots_root ON roots(root)")

    conn.commit()
    return conn


def populate_database(conn, data):
    """Populate the database with word-by-word data."""
    c = conn.cursor()

    print("Inserting surahs...")
    for i, (name_ar, name_en, ayah_count, rev_type, juz_start) in enumerate(SURAH_INFO):
        c.execute(
            "INSERT INTO surahs (id, name_ar, name_en, ayah_count, revelation_type, juz_start) VALUES (?, ?, ?, ?, ?, ?)",
            (i + 1, name_ar, name_en, ayah_count, rev_type, juz_start),
        )

    c.execute(
        "INSERT INTO sources (name, description, url) VALUES (?, ?, ?)",
        (
            "Quran.com API",
            "Quran word-by-word translation data (CC-BY-4.0)",
            "https://api.quran.com",
        ),
    )
    source_id = c.lastrowid

    print("Processing words...")
    word_map = {}
    for w in data:
        text = w["text"]
        if text not in word_map:
            c.execute(
                "INSERT INTO words (text, text_clean, translation, transliteration, position_in_ayah) VALUES (?, ?, ?, ?, ?)",
                (
                    text,
                    strip_diacritics(text),
                    w["translation"],
                    w["transliteration"],
                    w["position"],
                ),
            )
            word_map[text] = c.lastrowid
            c.execute(
                "INSERT INTO word_sources (word_id, source_id) VALUES (?, ?)",
                (word_map[text], source_id),
            )

    print("Inserting ayat and linking words...")
    ayah_data = {}
    for w in data:
        key = (w["surah"], w["ayah"])
        if key not in ayah_data:
            ayah_data[key] = {
                "text_uthmani": w.get("verse_text", ""),
                "word_count": 0,
                "words": [],
            }
        ayah_data[key]["word_count"] += 1
        ayah_data[key]["words"].append(w)

    progress_step = max(1, len(ayah_data) // 20)
    for i, ((surah, ayah), ayah_info) in enumerate(ayah_data.items()):
        if (i + 1) % progress_step == 0:
            print(f"  Progress: {i + 1}/{len(ayah_data)} ayat")

        c.execute(
            "INSERT INTO ayat (surah, ayah, text_uthmani, word_count) VALUES (?, ?, ?, ?)",
            (surah, ayah, ayah_info["text_uthmani"], ayah_info["word_count"]),
        )
        ayah_id = c.lastrowid

        for w in ayah_info["words"]:
            location = w.get("location") or f"{surah}:{ayah}:{w['position']}"
            c.execute(
                "INSERT INTO word_ayah (word_id, ayah_id, position, location) VALUES (?, ?, ?, ?)",
                (word_map[w["text"]], ayah_id, w["position"], location),
            )

    conn.commit()
    print("Database populated successfully!")


def verify_database(conn):
    """Verify the stage-1 database contents."""
    c = conn.cursor()
    print("\n=== التحقق من قاعدة البيانات (المرحلة 1) ===\n")

    for table in ("surahs", "ayat", "words", "word_ayah", "sources"):
        c.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"عدد سجلات {table}: {c.fetchone()[0]}")

    c.execute(
        "SELECT COUNT(*) FROM word_ayah WHERE location IS NOT NULL AND location != ''"
    )
    print(f"مواضع الكلمات مع location: {c.fetchone()[0]}")

    print("\n=== عينات ===\n")
    c.execute("""
        SELECT a.surah, a.ayah, wa.position, wa.location, w.text, w.translation
        FROM word_ayah wa
        JOIN words w ON wa.word_id = w.id
        JOIN ayat a ON wa.ayah_id = a.id
        WHERE a.surah = 1 AND a.ayah = 1
        ORDER BY wa.position
    """)
    for row in c.fetchall():
        print(f"  {row[0]}:{row[1]}:{row[2]} [{row[3]}] {row[4]} -> {row[5]}")


def main():
    print("=== بناء قاعدة بيانات القرآن الكريم (المرحلة 1) ===\n")
    print("Loading data...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} words")

    print("\nCreating database...")
    conn = create_database()

    print("\nPopulating database...")
    populate_database(conn, data)

    verify_database(conn)
    conn.close()
    print(f"\nتم بناء قاعدة البيانات بنجاح: {DB_PATH}")


if __name__ == "__main__":
    main()
