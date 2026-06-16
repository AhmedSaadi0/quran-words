# Quran Words - قاعدة بيانات كلمات القرآن الكريم

قاعدة بيانات احترافية لجميع كلمات القرآن الكريم مع الترجمة الإنجليزية والتحليل الصرفي.

## 📊 إحصائيات

| العدد | الوصف |
|-------|-------|
| 114 | سورة |
| 6,236 | آية |
| 77,429 | كلمة (مع التكرار) |
| 21,295 | كلمة فريدة |

## 📁 هيكل المشروع

```
quran-words/
├── README.md                 # هذا الملف
├── LICENSE                   # ترخيص MIT
├── .gitignore               # ملفات تجاهل Git
├── data/
│   └── quran_words.db       # قاعدة البيانات SQLite
├── scripts/
│   ├── download_quran.py    # سكربت تحميل البيانات
│   └── build_db.py          # سكربت بناء القاعدة
└── examples/
    └── queries.sql           # أمثلة على الاستعلامات
```

## 🚀 البدء السريع

### تحميل قاعدة البيانات
```bash
# استنساخ المستودع
git clone https://github.com/yourusername/quran-words.git
cd quran-words

# استخدام قاعدة البيانات مباشرة
sqlite3 data/quran_words.db
```

### بناء القاعدة من الصفر
```bash
# تحميل البيانات من Quran.com
python scripts/download_quran.py

# بناء قاعدة البيانات
python scripts/build_db.py
```

## 📋 هيكل قاعدة البيانات

### جدول `surahs` - السور
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | رقم السورة (1-114) |
| name_ar | TEXT | اسم السورة بالعربية |
| name_en | TEXT | اسم السورة بالإنجليزية |
| ayah_count | INTEGER | عدد الآيات |
| revelation_type | TEXT | مكية / مدنية |
| juz_start | INTEGER | رقم الجزء |

### جدول `ayat` - الآيات
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| surah | INTEGER | رقم السورة |
| ayah | INTEGER | رقم الآية |
| text_uthmani | TEXT | نص الآية (الرسم العثماني) |
| word_count | INTEGER | عدد الكلمات |

### جدول `words` - الكلمات
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| text | TEXT | الكلمة بالتشكيل |
| text_clean | TEXT | الكلمة بدون تشكيل |
| translation | TEXT | الترجمة الإنجليزية |
| transliteration | TEXT | الترقيم اللاتيني |
| root_id | INTEGER | معرف الجذر |

### جدول `roots` - الجذور
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| root | TEXT | الجذر العربي |

### جدول `word_ayah` - علاقات الكلمات-الآيات
| العمود | النوع | الوصف |
|--------|-------|-------|
| word_id | INTEGER | معرف الكلمة |
| ayah_id | INTEGER | معرف الآية |
| position | INTEGER | ترتيب الكلمة في الآية |

## 🔍 أمثلة على الاستعلامات

### البحث عن كلمة محددة
```sql
-- البحث عن كلمة "الله" في القرآن
SELECT w.text, w.translation, a.surah, a.ayah
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
WHERE w.text_clean LIKE '%ٱلله%'
ORDER BY a.surah, a.ayah;
```

### عرض سورة معينة
```sql
-- عرض سورة الفاتحة كاملة
SELECT a.ayah, wa.position, w.text, w.translation
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
WHERE a.surah = 1
ORDER BY a.ayah, wa.position;
```

### البحث بالجذر
```sql
-- البحث عن كلمات بجذر "ك ت ب"
SELECT w.text, w.translation
FROM words w
JOIN roots r ON w.root_id = r.id
WHERE r.root = 'كتب';
```

### إحصائيات
```sql
-- عدد الكلمات في كل سورة
SELECT s.name_ar, s.name_en, COUNT(DISTINCT w.id) as word_count
FROM surahs s
JOIN ayat a ON s.id = a.surah
JOIN word_ayah wa ON a.id = wa.ayah_id
JOIN words w ON wa.word_id = w.id
GROUP BY s.id
ORDER BY s.id;
```

### أكثر الكلمات تكراراً
```sql
-- أكثر 20 كلمة تكراراً في القرآن
SELECT w.text, w.translation, COUNT(*) as frequency
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
GROUP BY w.text
ORDER BY frequency DESC
LIMIT 20;
```

## 📊 مصادر البيانات

- **النص العربي**: [Quran.com API](https://api.quran.com) - الرسم العثماني
- **الترجمة الإنجليزية**: [Quran.com API](https://api.quran.com) - ترجمة كلمة بكلمة
- **عدد الكلمات**: 77,429 كلمة في 6,236 آية

## 🤝 المساهمة

مرحبا بك في المساهمة في هذا المشروع! يمكنك:
- تحسين الجذور العربية
- إضافة ترجمات بلغات أخرى
- تحسين التحليل الصرفي
- إصلاح الأخطاء

## 📄 الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE).

بيانات القرآن الكريم من [Quran.com](https://quran.com) مرخصة بموجب [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

## 🙏 الشكر

شكرا لموقع [Quran.com](https://quran.com) على توفير API مجاني لبيانات القرآن الكريم.
