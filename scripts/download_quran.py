#!/usr/bin/env python3
"""
Download Quran word-by-word data from Quran.com API.
Downloads all 114 surahs with word-by-word translations.
"""

import json
import time
import urllib.request
import urllib.error
import sys

BASE_URL = "https://api.quran.com/api/v4"

# Surah info (name, ayah_count, revelation_type)
SURAH_INFO = [
    ("الفاتحة", 7, "مكية"),
    ("البقرة", 286, "مدنية"),
    ("آل عمران", 200, "مدنية"),
    ("النساء", 176, "مدنية"),
    ("المائدة", 120, "مدنية"),
    ("الأنعام", 165, "مكية"),
    ("الأعراف", 206, "مكية"),
    ("الأنفال", 75, "مدنية"),
    ("التوبة", 129, "مدنية"),
    ("يونس", 109, "مكية"),
    ("هود", 123, "مكية"),
    ("يوسف", 111, "مكية"),
    ("الرعد", 43, "مدنية"),
    ("إبراهيم", 52, "مكية"),
    ("الحجر", 99, "مكية"),
    ("النحل", 128, "مكية"),
    ("الإسراء", 111, "مكية"),
    ("الكهف", 110, "مكية"),
    ("مريم", 98, "مكية"),
    ("طه", 135, "مكية"),
    ("الأنبياء", 112, "مكية"),
    ("الحج", 78, "مدنية"),
    ("المؤمنون", 118, "مكية"),
    ("النور", 64, "مدنية"),
    ("الفرقان", 77, "مكية"),
    ("الشعراء", 227, "مكية"),
    ("النمل", 93, "مكية"),
    ("القصص", 88, "مكية"),
    ("العنكبوت", 69, "مكية"),
    ("الروم", 60, "مكية"),
    ("لقمان", 34, "مكية"),
    ("السجدة", 30, "مكية"),
    ("الأحزاب", 73, "مدنية"),
    ("سبأ", 54, "مكية"),
    ("فاطر", 45, "مكية"),
    ("يس", 83, "مكية"),
    ("الصافات", 182, "مكية"),
    ("ص", 88, "مكية"),
    ("الزمر", 75, "مكية"),
    ("غافر", 85, "مكية"),
    ("فصلت", 54, "مكية"),
    ("الشورى", 53, "مكية"),
    ("الزخرف", 89, "مكية"),
    ("الدخان", 59, "مكية"),
    ("الجاثية", 37, "مكية"),
    ("الأحقاف", 35, "مكية"),
    ("محمد", 38, "مدنية"),
    ("الفتح", 29, "مدنية"),
    ("الحجرات", 18, "مدنية"),
    ("ق", 45, "مكية"),
    ("الذاريات", 60, "مكية"),
    ("الطور", 49, "مكية"),
    ("النجم", 62, "مكية"),
    ("القمر", 55, "مكية"),
    ("الرحمن", 78, "مدنية"),
    ("الواقعة", 96, "مكية"),
    ("الحديد", 29, "مدنية"),
    ("المجادلة", 22, "مدنية"),
    ("الحشر", 24, "مدنية"),
    ("الممتحنة", 13, "مدنية"),
    ("الصف", 14, "مدنية"),
    ("الجمعة", 11, "مدنية"),
    ("المنافقون", 11, "مدنية"),
    ("التغابن", 18, "مدنية"),
    ("الطلاق", 12, "مدنية"),
    ("التحريم", 12, "مدنية"),
    ("الملك", 30, "مكية"),
    ("القلم", 52, "مكية"),
    ("الحاقة", 28, "مكية"),
    ("ال المعارج", 44, "مكية"),
    ("نوح", 28, "مكية"),
    ("الجن", 28, "مكية"),
    ("المزمل", 20, "مكية"),
    ("المدثر", 56, "مكية"),
    ("القيامة", 40, "مكية"),
    ("الإنسان", 31, "مدنية"),
    ("المرسلات", 50, "مكية"),
    ("النبأ", 40, "مكية"),
    ("النازعات", 46, "مكية"),
    ("عبس", 42, "مكية"),
    ("التكوير", 17, "مكية"),
    ("الانفطار", 19, "مكية"),
    ("المطففين", 36, "مكية"),
    ("الانشقاق", 25, "مكية"),
    ("البروج", 22, "مكية"),
    ("الطارق", 17, "مكية"),
    ("الأعلى", 19, "مكية"),
    ("الغاشية", 26, "مكية"),
    ("الفجر", 30, "مكية"),
    ("البلد", 20, "مكية"),
    ("الشمس", 15, "مكية"),
    ("الليل", 21, "مكية"),
    ("الضحى", 11, "مكية"),
    ("الشرح", 8, "مكية"),
    ("التين", 8, "مكية"),
    ("العلق", 19, "مكية"),
    ("القدر", 5, "مكية"),
    ("البينة", 8, "مدنية"),
    ("الزلزلة", 8, "مدنية"),
    ("العاديات", 11, "مكية"),
    ("القارعة", 11, "مكية"),
    ("التكاثر", 8, "مكية"),
    ("العصر", 3, "مكية"),
    ("الهمزة", 9, "مكية"),
    ("الفيل", 5, "مكية"),
    ("قريش", 4, "مكية"),
    ("الماعون", 7, "مكية"),
    ("الكوثر", 3, "مكية"),
    ("الكافرون", 6, "مكية"),
    ("النصر", 3, "مدنية"),
    ("المسد", 5, "مكية"),
    ("الإخلاص", 4, "مكية"),
    ("الفلق", 5, "مكية"),
    ("الناس", 6, "مكية"),
]


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuranDB/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                print(f"  FAILED: {url} - {e}", file=sys.stderr)
                return None


def download_surah(surah_num):
    """Download all ayahs for a surah with word-by-word data."""
    url = f"{BASE_URL}/verses/by_chapter/{surah_num}?language=en&words=true&per_page=999&fields=text_uthmani&word_fields=text_uthmani,translation,transliteration,location"
    data = fetch_json(url)
    if not data or "verses" not in data:
        return None
    return data["verses"]


def main():
    all_data = []
    total_words = 0

    print(f"Downloading Quran word-by-word data from Quran.com API...")
    print(f"Total surahs: {len(SURAH_INFO)}\n")

    for i, (surah_name, ayah_count, rev_type) in enumerate(SURAH_INFO):
        surah_num = i + 1
        print(
            f"[{surah_num:3d}/114] {surah_name} ({ayah_count} ayahs)...",
            end=" ",
            flush=True,
        )

        verses = download_surah(surah_num)
        if not verses:
            print("FAILED")
            continue

        surah_words = 0
        for verse in verses:
            verse_num = verse["verse_number"]
            words = verse.get("words", [])
            for word in words:
                if word.get("char_type_name") != "word":
                    continue
                word_data = {
                    "surah": surah_num,
                    "ayah": verse_num,
                    "position": word["position"],
                    "location": word.get("location", ""),
                    "text": word.get("text_uthmani", ""),
                    "translation": word.get("translation", {}).get("text", ""),
                    "transliteration": word.get("transliteration", {}).get("text", ""),
                    "verse_text": verse.get("text_uthmani", ""),
                }
                all_data.append(word_data)
                surah_words += 1

        total_words += surah_words
        print(f"{surah_words} words")
        time.sleep(0.3)  # Rate limiting

    # Save to file
    output_path = "/home/ahmed/0/quran/quran_words_wbw.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done! ===")
    print(f"Total words: {total_words}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
