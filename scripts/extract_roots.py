#!/usr/bin/env python3
"""
Extract Arabic roots from Quran words.
This script extracts the 3-letter root from Arabic words using common patterns.
"""
import sqlite3
import re
import json

# Common Arabic prefixes to remove
PREFIXES = [
    'وَ', 'فَ', 'بِ', 'كَ', 'لَ', 'تَ', 'يَ', 'نَ', 'أَ', 'إِ',
    'سَ', 'لَم', 'لَن', 'إِن', 'أَن', 'كَأَن', 'لَكِن', 'وَلَ',
    'فَلَ', 'بِمَا', 'لِمَا', 'كَمَا', 'وَمَا', 'فَمَا',
]

# Common Arabic suffixes to remove
SUFFIXES = [
    'ُونَ', 'ِينَ', 'َانِ', 'َاتٌ', 'َاتِ', 'َةٌ', 'َةِ',
    'ُهُم', 'ُهُنَّ', 'ُكُم', 'ُكُنَّ', 'ِي', 'ُكَ', 'ُهُ',
    'َهُ', 'َهَا', 'َهُم', 'َهُنَّ', 'َكَ', 'َكِ', 'َكُم',
    'َكُنَّ', 'َنَا', 'ُنَا', 'َانَا',
]

# Simple root mapping for common words
ROOT_MAP = {
    'بِسْمِ': 'بسم',
    'ٱللَّهِ': 'الله',
    'ٱللَّهُ': 'الله',
    'ٱللَّهَ': 'الله',
    'لِلَّهِ': 'الله',
    'ٱلرَّحْمَـٰنِ': 'رحم',
    'ٱلرَّحِيمِ': 'رحم',
    'ٱلْحَمْدُ': 'حمد',
    'رَبِّ': 'ربب',
    'ٱلْعَـٰلَمِينَ': 'علم',
    'مَـٰلِكِ': 'ملك',
    'يَوْمِ': 'يوم',
    'ٱلدِّينِ': 'دين',
    'إِيَّاكَ': 'وءك',
    'نَعْبُدُ': 'عبد',
    'وَإِيَّاكَ': 'وءك',
    'نَسْتَعِينُ': 'عون',
    'ٱهْدِنَا': 'هدي',
    'ٱلصِّرَٰطَ': 'صرط',
    'ٱلْمُسْتَقِيمَ': 'قيم',
    'صِرَٰطَ': 'صرط',
    'ٱلَّذِينَ': 'الذين',
    'أَنْعَمْتَ': 'نعم',
    'عَلَيْهِمْ': 'علي',
    'غَيْرِ': 'غير',
    'ٱلْمَغْضُوبِ': 'غضب',
    'وَلَا': 'ولو',
    'ٱلضَّآلِّينَ': 'ضلل',
}


def strip_diacritics(text):
    """Remove Arabic diacritics from text."""
    diacritics = re.compile(r'[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed]')
    return diacritics.sub('', text)


def extract_root_simple(word_text):
    """
    Simple root extraction using heuristic approach.
    This is not perfect but works for most common cases.
    """
    # Check if we have a mapping
    if word_text in ROOT_MAP:
        return ROOT_MAP[word_text]
    
    # Remove diacritics
    clean = strip_diacritics(word_text)
    
    # Remove hamzat wasl and replace with alef
    clean = clean.replace('ٱ', 'ا')
    
    # Common patterns to extract root
    patterns = [
        # Pattern: يفعل (present tense)
        (r'^ي(.{3})ُ', 1),
        # Pattern: تفعل (present tense)
        (r'^ت(.{3})ُ', 1),
        # Pattern: نفعل (present tense)
        (r'^ن(.{3})ُ', 1),
        # Pattern: أفعل (present tense)
        (r'^أ(.{3})ُ', 1),
        # Pattern: افعل (imperative)
        (r'^ا(.{3})ُ', 1),
        # Pattern: فعل (past tense)
        (r'^(.{3})َ', 0),
        # Pattern: فاعل (active participle)
        (r'^فَاعِل$', None),
        # Pattern: مفعل (passive participle)
        (r'^م(.{3})ِ', 1),
        # Pattern: اسم (noun)
        (r'^ا(.{3})ِ', 1),
    ]
    
    for pattern, group in patterns:
        match = re.match(pattern, clean)
        if match and group is not None:
            root = match.group(group)
            if len(root) == 3:
                return root
    
    # If no pattern matched, try to extract 3 consecutive consonants
    consonants = re.findall(r'[بتثجحخدذرزسشصضطظعغفقكلمنهوي]', clean)
    if len(consonants) >= 3:
        return ''.join(consonants[:3])
    
    # Last resort: return the clean word
    return clean


def process_database(db_path):
    """Process the database and extract roots for all words."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Clear existing roots
    print("Clearing existing roots...")
    c.execute("DELETE FROM roots")
    c.execute("DELETE FROM word_roots")
    c.execute("UPDATE words SET root_id = NULL")
    conn.commit()
    
    print("Processing words to extract roots...")
    
    # Get all words
    c.execute("SELECT id, text, text_clean FROM words")
    words = c.fetchall()
    
    # Create root map
    root_map = {}
    root_id_counter = 1
    
    # First, insert all roots
    print("Extracting roots...")
    for word_id, text, text_clean in words:
        root = extract_root_simple(text)
        if root not in root_map:
            root_map[root] = root_id_counter
            c.execute("INSERT INTO roots (id, root) VALUES (?, ?)", (root_id_counter, root))
            root_id_counter += 1
    
    # Update words with root_id
    print("Updating words with root_id...")
    for word_id, text, text_clean in words:
        root = extract_root_simple(text)
        root_id = root_map[root]
        c.execute("UPDATE words SET root_id = ? WHERE id = ?", (root_id, word_id))
    
    conn.commit()
    
    # Print statistics
    c.execute("SELECT COUNT(*) FROM roots")
    root_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM words")
    word_count = c.fetchone()[0]
    
    print(f"\nDone!")
    print(f"Total words: {word_count}")
    print(f"Total roots: {root_count}")
    
    # Show sample roots
    print("\nSample roots:")
    c.execute("SELECT root, COUNT(*) as cnt FROM roots GROUP BY root ORDER BY cnt DESC LIMIT 20")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]} words")
    
    conn.close()


if __name__ == "__main__":
    db_path = "/home/ahmed/0/quran/quran_words.db"
    process_database(db_path)
