# Quran Words - قاعدة بيانات كلمات القرآن الكريم

قاعدة بيانات احترافية لجميع كلمات القرآن الكريم مع الترجمة الإنجليزية والتحليل الصرفي والمعاني العربية.

## 📊 إحصائيات

| العدد | الوصف |
|-------|-------|
| 114 | سورة |
| 6,236 | آية |
| 77,429 | موضع كلمة (مع التكرار) |
| 21,295 | كلمة فريدة |
| ~1,700 | جذر لغوي (مدقق من المتن النحوي) |
| 77,429 | تحليل صرفي (لكل موضع كلمة) |
| 56,606 | مدخل معجمي للمعاني العربية |

## 📁 هيكل المشروع

```
quran-words/
├── README.md                 # هذا الملف
├── LICENSE                   # ترخيص MIT
├── .gitignore               # ملفات تجاهل Git
├── data/
│   ├── quran_words.db       # قاعدة البيانات SQLite
│   ├── quranic_corpus_morphology.json   # بيانات المتن النحوي المحللة
│   ├── arabic_roots.json    # معاني الجذور العربية
│   └── quranic-corpus-morphology-0.4.txt # الملف الخام للمتن
├── scripts/
│   ├── download_quran.py    # سكربت تحميل الكلمات من Quran.com API
│   ├── fetch_corpus.py      # سكربت جلب المتن النحوي (Quranic Arabic Corpus)
│   ├── fetch_arabic_roots.py# سكربت جلب معاني الجذور العربية
│   ├── build_db.py          # سكربت بناء القاعدة (المرحلة 1)
│   └── build_morphology.py  # سكربت التحليل الصرفي والمعاني (المرحلة 2)
└── examples/
    └── queries.sql           # أمثلة على الاستعلامات
```

## 🚀 البدء السريع

```bash
# استخدام قاعدة البيانات مباشرة
sqlite3 data/quran_words.db
```

### بناء القاعدة من الصفر (خطوتان)

```bash
# 1) تحميل البيانات:
python scripts/download_quran.py      # كلمات القرآن مع الترجمة (Quran.com)
python scripts/fetch_corpus.py        # المتن النحوي (Quranic Arabic Corpus)
python scripts/fetch_arabic_roots.py  # معاني الجذور (المعاجم الكلاسيكية)

# 2) بناء القاعدة:
python scripts/build_db.py            # المرحلة 1: السور والآيات والكلمات
python scripts/build_morphology.py    # المرحلة 2: الجذور والصرف والمعاني
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

### جدول `words` - الكلمات الفريدة
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| text | TEXT | الكلمة بالتشكيل |
| text_clean | TEXT | الكلمة بدون تشكيل |
| translation | TEXT | الترجمة الإنجليزية |
| transliteration | TEXT | الترقيم اللاتيني |

### جدول `word_ayah` - علاقات الكلمات-الآيات
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| word_id | INTEGER | معرف الكلمة |
| ayah_id | INTEGER | معرف الآية |
| position | INTEGER | ترتيب الكلمة في الآية |
| location | TEXT | موقع المتن النحوي (سورة:آية:كلمة) |

### جدول `roots` - الجذور
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| root | TEXT | الجذر العربي (مدقق من المتن النحوي) |

### جدول `lemmas` - الأصول اللغوية
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| lemma_ar | TEXT | الأصل اللغوي بالعربية |
| lemma_bw | TEXT | الأصل بترقيم Buckwalter |

### جدول `word_morphology` - التحليل الصرفي (لكل موضع)
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| word_ayah_id | INTEGER | موضع الكلمة |
| pos | TEXT | نوع الكلمة (N, V, ADJ, P...) |
| form | TEXT | الوزن الصرفي (I-XV) |
| aspect | TEXT | الصيغة (PERF/IMPF/IMPV) |
| mood | TEXT | الحالة (JUS/SUB...) |
| voice | TEXT | المعلوم/المجهول (ACT/PASS) |
| person / gender / number | TEXT | الشخص والجنس والعدد |
| grammatical_case | TEXT | الإعراب (NOM/ACC/GEN) |
| state | TEXT | التعريف/التنكير (DEF/INDEF) |
| derivation | TEXT | الاشتقاق (PCPL/VN) |
| root_id | INTEGER | الجذر |
| lemma_id | INTEGER | الأصل اللغوي |
| segments | TEXT | مقاطع الكلمة (سابقة/جذر/لاحقة) JSON |

### جدول `root_meanings` - معاني الجذور
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| root_id | INTEGER | الجذر |
| definition | TEXT | المعنى العربي |
| book_name | TEXT | اسم المعجم (مفردات الراغب، لسان العرب...) |
| source_url | TEXT | رابط المصدر |

### جدول `sources` - المصادر
| العمود | النوع | الوصف |
|--------|-------|-------|
| id | INTEGER | معرف فريد |
| name | TEXT | اسم المصدر |
| description | TEXT | الوصف |
| url | TEXT | الرابط |

## 🔍 أمثلة على الاستعلامات

```sql
-- عرض سورة الفاتحة مع التحليل الصرفي
SELECT a.ayah, wa.position, w.text, wm.pos, r.root, wm.form, wm.grammatical_case
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN ayat a ON wa.ayah_id = a.id
LEFT JOIN word_morphology wm ON wm.word_ayah_id = wa.id
LEFT JOIN roots r ON r.id = wm.root_id
WHERE a.surah = 1
ORDER BY a.ayah, wa.position;

-- المعنى العربي لجذر "رحم" من المعاجم الكلاسيكية
SELECT r.root, rm.book_name, rm.definition
FROM roots r
JOIN root_meanings rm ON rm.root_id = r.id
WHERE r.root = 'رحم';

-- الأفعال الماضية المبنية للمجهول
SELECT DISTINCT w.text, w.translation, r.root
FROM word_ayah wa
JOIN words w ON wa.word_id = w.id
JOIN word_morphology wm ON wm.word_ayah_id = wa.id
JOIN roots r ON r.id = wm.root_id
WHERE wm.aspect = 'PERF' AND wm.voice = 'PASS';
```

المزيد في [examples/queries.sql](examples/queries.sql).

## 📊 مصادر البيانات

| المصدر | البيانات | الترخيص |
|--------|----------|---------|
| [Quran.com API](https://api.quran.com) | النص العثماني، الترجمة والترقيم كلمة بكلمة | CC-BY-4.0 |
| [Quranic Arabic Corpus](http://corpus.quran.com) (جامعة ليدز، v0.4) | التحليل الصرفي لكل كلمة: الجذر والأصل ونوع الكلمة والتصريف | GPL |
| [Arabic Lexicon](http://arabiclexicon.hawramani.com) | معاني الجذور من: مفردات غريب القرآن للراغب، لسان العرب، تاج العروس، الصحاح، القاموس المحيط | GPL-3.0 |

ملاحظة: بنية المتن النحوي تتطلب ذكر المصدر والرابط في أي عمل مشتق (شاهد جدول `sources`).

## 🤝 المساهمة

مرحباً بك في المساهمة في هذا المشروع! يمكنك:
- إضافة ترجمات بلغات أخرى
- تحسين ربط الجذور بالمعاجم
- إضافة معاجم جديدة للمعاني
- إصلاح الأخطاء

## 📄 الترخيص

هذا المشروع مرخص بموجب [MIT License](LICENSE).

- بيانات القرآن الكريم من [Quran.com](https://quran.com) مرخصة بموجب [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).
- المتن النحوي [Quranic Arabic Corpus](http://corpus.quran.com) مرخص بموجب GPL (انظر [شروط الاستخدام](http://corpus.quran.com/download)).
- بيانات المعاني من [arabic-roots](https://huggingface.co/datasets/MohamedRashad/arabic-roots) مرخصة بموجب GPL-3.0.

## 🙏 الشكر

شكراً لموقع [Quran.com](https://quran.com) و[Quranic Arabic Corpus](http://corpus.quran.com) على توفير بيانات مفتوحة عالية الجودة.