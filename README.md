# Quran Words - قاعدة بيانات كلمات القرآن الكريم

قاعدة بيانات احترافية ومتكاملة لجميع كلمات القرآن الكريم — من النص العثماني إلى التحليل الصرفي الدقيق، مروراً بالجذور والمصادر والمشتقات والمعاني من المعاجم الكلاسيكية.

> الهدف: أن تكتب `SELECT` واحداً لتحصل على الكلمة + جذرها + مصدرها + كل مشتقاتها + معناها من لسان العرب.

---

## 📊 إحصائيات

| العدد | الوصف |
|-------|-------|
| 114 | سورة |
| 6,236 | آية |
| 77,429 | موضع كلمة (مع التكرار) |
| 21,295 | كلمة فريدة (بالتشكيل) |
| 1,642 | جذر لغوي (مدقق من المتن النحوي QAC) |
| 4,832 | أصل لغوي (lemma) |
| 77,429 | تحليل صرفي لكل موضع (POS, وزن, إعراب...) |
| 5,273 | مصدر (masdar) مولّد/موثق لكل جذر |
| 16,245 | مشتق (اسم فاعل/مفعول/مبالغة...) لكل جذر |
| 66,436 | رابط كلمة ← مصدر |
| 9,639 | مدخل معجمي للمعاني العربية |
| 56,606 | مدخل خام من المعاجم (قبل الربط) |

---

## ✨ ما الجديد؟ (المرحلة 3)

* أُضيف **جدول `masadir`** — مصدر كل جذر/كلمة: المنصوص في القرآن (`VN`) + المولّد بالأوزان (`تفعيل، إفعال، افتعال، استفعال...`) مع تحقّق بـ `CAMeL Tools (CALIMA-Star)`.
* أُضيف **جدول `derivatives`** — كل المشتقات الشائعة للجذر (`فاعل، مفعول، فعّال، فعيل، مِفعال...`) مع تمييز ما ورد فعلاً في القرآن (`is_quranic`) وما صحّحه CAMeL.
* أُضيف **جدول `word_masdar`** — يربط كل موضع كلمة بمصدر(مصادر) جذره.
* البديل `Farasa` تم تقييمه واستُبعد لصالح `CAMeL Tools` (أدق على الرسم القرآني، توليد صرفي حقيقي، MIT).

---

## 📁 هيكل المشروع

```
quran-words/
├── README.md
├── LICENSE
├── data/
│   ├── quran_words.db                      # SQLite النهائية (107 MB)
│   ├── quranic_corpus_morphology.json      # 77,429 token محلّل من QAC
│   ├── quranic-corpus-morphology-0.4.txt   # الخام من corpus.quran.com
│   ├── arabic_roots.json                   # 26,067 جذر بمعانيه (162 MB)
│   └── arabic_roots.parquet                # الأصل من HF (79 MB)
├── scripts/
│   ├── download_quran.py                   # تحميل الكلمات من Quran.com API
│   ├── fetch_corpus.py                     # جلب المتن النحوي QAC v0.4
│   ├── fetch_arabic_roots.py               # جلب معاني الجذور (HF)
│   ├── build_db.py                         # المرحلة 1: سور/آيات/كلمات
│   ├── build_morphology.py                 # المرحلة 2: صرف + جذور + معاني
│   └── build_masadir_derivatives.py        # المرحلة 3: مصادر + مشتقات (CAMeL)
└── examples/
    ├── queries.sql                         # 12 استعلاماً أساسياً
    └── masadir_queries.sql                 # 8 استعلامات للمصادر/المشتقات
```

---

## 🚀 البدء السريع

```bash
# 1) استخدام مباشر بدون بناء
sqlite3 data/quran_words.db
sqlite> SELECT * FROM masadir WHERE root='كتب' LIMIT 5;
sqlite> SELECT * FROM derivatives WHERE root='علم' AND is_quranic=1;

# 2) بايثون
import sqlite3
conn = sqlite3.connect("data/quran_words.db")
conn.execute("SELECT masdar_plain FROM masadir WHERE root='رحم'").fetchall()
```

### بناء القاعدة من الصفر (3 مراحل)

```bash
# المتطلبات
python --version  # >=3.11
pip install --user camel-tools pyarrow  # pyarrow لمعاني الجذور
camel_data -i morphology-db-msa-r13      # ~40 MB (CAMeL) - إجباري للمصادر

# 1) تحميل البيانات (مرة واحدة)
python scripts/download_quran.py        # -> /tmp/quran_words_wbw.json
python scripts/fetch_corpus.py          # -> data/quranic_corpus_morphology.json
python scripts/fetch_arabic_roots.py    # -> data/arabic_roots.json (79 MB -> 162 MB)

# 2) بناء القاعدة
python scripts/build_db.py              # المرحلة 1: surahs, ayat, words, word_ayah
python scripts/build_morphology.py      # المرحلة 2: roots, lemmas, word_morphology, root_meanings

# 3) توليد المصادر والمشتقات (يحتاج CAMeL)
python scripts/build_masadir_derivatives.py  # -> masadir, derivatives, word_masdar
```

> **ملاحظة الحجم:** `camel-tools` نفسها 0.12MB لكنها تتطلب `scikit-learn`/`camel-kenlm` (~12MB) + قاعدة `calima-msa-r13` (~40MB). `torch` (526MB) مطلوب فقط لنموذج `BERT` السياقي وغير لازم لهذا السكربت.

---

## 📋 هيكل قاعدة البيانات

### `surahs` - السور
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | رقم السورة 1-114 |
| name_ar | TEXT | الاسم بالعربية |
| name_en | TEXT | الاسم بالإنجليزية |
| ayah_count | INTEGER | عدد الآيات |
| revelation_type | TEXT | مكية / مدنية |
| juz_start | INTEGER | بداية الجزء |

### `ayat` - الآيات
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| surah | INTEGER | رقم السورة |
| ayah | INTEGER | رقم الآية |
| text_uthmani | TEXT | النص بالرسم العثماني |
| word_count | INTEGER | عدد الكلمات |

### `words` - الكلمات الفريدة
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف |
| text | TEXT | الكلمة بالتشكيل |
| text_clean | TEXT | بدون تشكيل |
| translation | TEXT | الترجمة الإنجليزية |
| transliteration | TEXT | الترقيم اللاتيني |

### `word_ayah` - تموضع الكلمات
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف |
| word_id | INTEGER | FK -> words |
| ayah_id | INTEGER | FK -> ayat |
| position | INTEGER | الترتيب في الآية |
| location | TEXT | `سورة:آية:كلمة` (QAC) |

### `roots` - الجذور (مدققة)
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف |
| root | TEXT | الجذر عربي (مثل `كتب`) |

### `lemmas` - الأصول
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف |
| lemma_ar | TEXT | الأصل بالعربية |
| lemma_bw | TEXT | Buckwalter |

### `word_morphology` - التحليل الصرفي لكل موضع
| العمود | النوع | الوصف |
|--------|-------|-------|
| word_ayah_id | INTEGER | FK |
| pos | TEXT | `N, V, ADJ, P, PN...` |
| form | TEXT | الوزن `I-XV` |
| aspect/mood/voice | TEXT | `PERF/IMPF`, `JUS/SUB`, `ACT/PASS` |
| person/gender/number | TEXT | |
| grammatical_case | TEXT | `NOM/ACC/GEN` |
| state | TEXT | `DEF/INDEF` |
| derivation | TEXT | `VN` (مصدر) / `PCPL` (اسم فاعل/مفعول) |
| root_id / lemma_id | INTEGER | FK |
| segments | TEXT | JSON للمقاطع |

### `root_meanings` - معاني الجذور الكلاسيكية
| العمود | النوع | الوصف |
|--------|-------|-------|
| root_id | INTEGER | FK |
| definition | TEXT | المعنى |
| book_name | TEXT | `لسان العرب، تاج العروس، المفردات...` (9 كتب) |
| source_url | TEXT | hawramani.com |

### `masadir` - المصادر (جديد)
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف |
| root_id | INTEGER | FK -> roots |
| root | TEXT | الجذر نصاً |
| form | TEXT | الوزن `I-XV` |
| lemma_id | INTEGER | إن ارتبط بـ lemma منصوص |
| masdar_ar | TEXT | المصدر بالتشكيل |
| masdar_plain | TEXT | بدون تشكيل |
| pattern | TEXT | الوزن (`فَعَالة، تفعيل، افتعال...`) |
| is_attested | BOOLEAN | 1 إذا ورد كـ `VN` في القرآن |
| source | TEXT | `quran_vn` / `camel+pattern` / `pattern` |
| confidence | REAL | 0-1 |

### `derivatives` - المشتقات (جديد)
| العمود | النوع | الوصف |
|--------|-------|-------|
| root_id | INTEGER | FK |
| root | TEXT | الجذر |
| pattern | TEXT | الوزن (`فاعل، مفعول، فعّال...`) |
| derivative_type | TEXT | `اسم فاعل، اسم مفعول، صفة مشبهة...` |
| form_ar | TEXT | الصيغة بالتشكيل |
| form_plain | TEXT | بدون تشكيل |
| pos | TEXT | `N/ADJ` |
| is_quranic | BOOLEAN | هل ورد في القرآن؟ |
| camel_valid | BOOLEAN | هل صحّحه CAMeL؟ |
| example_word_id | INTEGER | FK -> words (إن قرآني) |
| source | TEXT | `camel+pattern` / `quran+pattern` |

### `word_masdar` - ربط الموضع بالمصدر (جديد)
| العمود | النوع | الوصف |
|--------|-------|-------|
| word_ayah_id | INTEGER | FK -> word_ayah |
| masdar_id | INTEGER | FK -> masadir |

### `sources` - المصادر الببليوغرافية
| id | name | url |
|----|------|-----|
| 1 | Quran.com API | api.quran.com |
| 2 | Quranic Arabic Corpus v0.4 | corpus.quran.com |
| 3 | Arabic Lexicon (Hawramani) | arabiclexicon.hawramani.com |
| 4 | CAMeL Tools + CALIMA-Star | github.com/CAMeL-Lab/CAMeL_Tools |

---

## 🔍 أمثلة على الاستعلامات

### أساسي
```sql
-- سورة الفاتحة مع التحليل
SELECT a.ayah, wa.position, w.text, wm.pos, r.root, wm.form
FROM word_ayah wa
JOIN words w ON wa.word_id=w.id
JOIN ayat a ON wa.ayah_id=a.id
LEFT JOIN word_morphology wm ON wm.word_ayah_id=wa.id
LEFT JOIN roots r ON r.id=wm.root_id
WHERE a.surah=1 ORDER BY a.ayah, wa.position;

-- معنى جذر
SELECT rm.book_name, rm.definition FROM roots r
JOIN root_meanings rm ON rm.root_id=r.id WHERE r.root='رحم' LIMIT 3;
```

### مصادر ومشتقات (جديد)
```sql
-- كل مصادر جذر كتب
SELECT masdar_ar, pattern, form, is_attested, source
FROM masadir WHERE root='كتب' ORDER BY is_attested DESC, confidence DESC;
-- كَتَابة [فَعَالة/I], كُتُب [فَعْل/I], اِكْتِتاب [افتعال/VIII], مُكاتَبَة [مفاعلة/III]

-- مشتقات علم القرآنية
SELECT form_ar, derivative_type, pattern FROM derivatives
WHERE root='علم' AND is_quranic=1;
-- عالِم (فاعل), مَعْلُوم (مفعول), عَلِيم (فعيل)

-- مصدر كل كلمة في آية
SELECT w.text, r.root, m.masdar_plain, m.pattern
FROM word_ayah wa
JOIN words w ON wa.word_id=w.id
JOIN word_morphology wm ON wm.word_ayah_id=wa.id
JOIN roots r ON r.id=wm.root_id
JOIN masadir m ON m.root_id=r.id
WHERE wa.ayah_id=1 GROUP BY wa.id LIMIT 5;

-- البحث بالمصدر: كل آيات فيها مصدر "رحمة"
SELECT DISTINCT a.surah, a.ayah, a.text_uthmani
FROM masadir m
JOIN word_masdar wmd ON wmd.masdar_id=m.id
JOIN word_ayah wa ON wa.id=wmd.word_ayah_id
JOIN ayat a ON a.id=wa.ayah_id
WHERE m.masdar_plain='رحمة' LIMIT 5;
```

المزيد في [`examples/queries.sql`](examples/queries.sql) و [`examples/masadir_queries.sql`](examples/masadir_queries.sql).

---

## 📊 مصادر البيانات والتراخيص

| المصدر | البيانات | الترخيص |
|--------|----------|---------|
| [Quran.com API](https://api.quran.com) | النص العثماني والترجمة كلمة بكلمة | CC-BY-4.0 |
| [Quranic Arabic Corpus](http://corpus.quran.com) (Leeds) | تحليل صرفي لكل كلمة (جذر، lemma، وزن...) | GPL |
| [Arabic Lexicon - Hawramani](http://arabiclexicon.hawramani.com) / [arabic-roots HF](https://huggingface.co/datasets/MohamedRashad/arabic-roots) | معاني الجذور من 9 معاجم (الراغب، لسان العرب، تاج العروس، الصحاح...) | GPL-3.0 |
| [CAMeL Tools + CALIMA-Star](https://github.com/CAMeL-Lab/CAMeL_Tools) | تحقق/توليد صرفي للمصادر والمشتقات | MIT / GPL-2.0 (DB) |

> **تنبيه GPL:** المتن النحوي ومعاني الجذور GPL؛ عند التوزيع يجب ذكر المصدر والرابط (جدول `sources`) وتوفير الكود المصدري للتعديلات.

---

## 🛠️ قرار التصميم: لماذا CAMeL وليس Farasa؟

| المعيار | Farasa | CAMeL Tools (اختيارنا) |
|---------|--------|------------------------|
| دقة على الرسم العثماني | متوسطة (مدرب على MSA) | عالية (CALIMA-Star يغطي الكلاسيكية) |
| توليد المصدر | يصنّف فقط | يولّد + يحقّق بالأوزان |
| توليد المشتقات | لا | نعم (`فاعل، مفعول...`) |
| الترخيص | بحثي مقيد | MIT مفتوح |
| الحجم | Java/Docker + API | `pip install` + 40MB DB |

تم الاحتفاظ بـ QAC كـ ground truth وعدم استبدال جذوره بأي محلل آلي.

---

## 🤝 المساهمة

مرحباً بالمساهمات:
- إضافة ترجمات بلغات أخرى
- تحسين قوائم الأوزان (`MASDAR_PATTERNS_BY_FORM` في `build_masadir_derivatives.py`)
- إضافة معاجم جديدة
- إصلاح التشكيل للمصادر

---

## 📄 الترخيص

كود المشروع: **MIT** ([LICENSE](LICENSE)).
البيانات: انظر الجدول أعلاه (CC-BY-4.0 / GPL / GPL-3.0 / MIT).

---

## 🙏 الشكر

[Quran.com](https://quran.com) و [Quranic Arabic Corpus](http://corpus.quran.com) و [Hawramani](http://arabiclexicon.hawramani.com) و [CAMeL Lab - NYU Abu Dhabi](https://github.com/CAMeL-Lab/CAMeL_Tools) على البيانات المفتوحة.
