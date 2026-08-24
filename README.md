# Quran Words - قاعدة بيانات كلمات القرآن الكريم

<p align="center">
  <a href="https://github.com/AhmedSaadi0/quran-words"><img src="https://img.shields.io/github/repo-size/AhmedSaadi0/quran-words?label=%D8%AD%D8%AC%D9%85%20%D8%A7%D9%84%D9%83%D9%88%D8%AF&color=0e75b6" alt="repo size"></a>
  <a href="https://github.com/AhmedSaadi0/quran-words"><img src="https://img.shields.io/badge/DB-114%20MB-blue" alt="db size"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-%3E%3D3.11-3776AB" alt="python"></a>
  <a href="https://nextjs.org"><img src="https://img.shields.io/badge/next.js-16-black" alt="nextjs"></a>
</p>

قاعدة بيانات احترافية ومتكاملة لجميع كلمات القرآن الكريم — من النص العثماني إلى التحليل الصرفي الدقيق، مروراً بالجذور والمصادر والمشتقات والمعاني من المعاجم الكلاسيكية.

> الهدف: أن تكتب `SELECT` واحداً لتحصل على الكلمة + جذرها + مصدرها + كل مشتقاتها + معناها من لسان العرب.

> 📦 **حجم المستودع:** الكود ~**4.6 MB** (حسب GitHub API `size: 4704 KB`) + البيانات عبر **Git LFS** ~**415 MB** ( `quran_words.db 114 MB` + `arabic_roots.json 169 MB` + `arabic_roots.parquet 83 MB` + `quranic_corpus_morphology.json 43 MB` + `quranic-corpus-morphology-0.4.txt 6.2 MB`). بعد `git clone --depth 1` ستحتاج `git lfs pull` لسحب ملفات `data/` كاملة. كامل المشروع على القرص بعد التثبيت ~**1.7 GB** (مع `.git/lfs` و `node_modules` و `.venv`).

---

## 📑 الفهرس

- [إحصائيات](#-إحصائيات)
- [ما الجديد؟](#-ما-الجديد-المرحلة-3)
- [هيكل المشروع](#-هيكل-المشروع)
- [المتطلبات](#️-المتطلبات)
- [الاستنساخ السريع](#-الاستنساخ-السريع)
- [البدء السريع بدون بناء](#-البدء-السريع-بدون-بناء)
- [تشغيل الخلفية Django](#️-تشغيل-الخلفية-django--drf)
- [تشغيل الواجهة Next.js](#-تشغيل-الواجهة-nextjs)
- [التشغيل المتكامل](#-التشغيل-المتكامل-الخلفية--الواجهة)
- [بناء القاعدة من الصفر](#️-بناء-القاعدة-من-الصفر-3-مراحل)
- [هيكل قاعدة البيانات](#-هيكل-قاعدة-البيانات)
- [واجهة البرمجة API](#-واجهة-البرمجة-api)
- [أمثلة على الاستعلامات](#-أمثلة-على-الاستعلامات)
- [مصادر البيانات والتراخيص](#-مصادر-البيانات-والتراخيص)
- [لماذا CAMeL وليس Farasa؟](#️-قرار-التصميم-لماذا-camel-وليس-farasa)
- [استكشاف الأخطاء](#-استكشاف-الأخطاء)
- [المساهمة والترخيص](#-المساهمة)

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
├── .gitattributes
├── data/
│   ├── quran_words.db
│   ├── quranic_corpus_morphology.json
│   ├── quranic-corpus-morphology-0.4.txt
│   ├── arabic_roots.json
│   └── arabic_roots.parquet
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   ├── core/
│   ├── quran/
│   ├── words/
│   ├── morphology/
│   ├── roots/
│   ├── derivatives/
│   ├── sources/
│   ├── search/
│   ├── .venv/
│   └── scripts/smoke_api.py
├── frontend/
│   ├── package.json
│   ├── vendor/next-16.3.2.tgz
│   ├── .npmrc
│   ├── next.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── search/page.tsx
│   │   │   ├── roots/[root]/page.tsx
│   │   │   ├── words/[id]/page.tsx
│   │   │   ├── surahs/[id]/page.tsx
│   │   │   ├── guide/morphology/
│   │   │   └── sources/page.tsx
│   │   ├── components/
│   │   └── lib/
│   │       ├── api.ts
│   │       └── normalize.ts
│   └── public/
├── scripts/
│   ├── download_quran.py
│   ├── fetch_corpus.py
│   ├── fetch_arabic_roots.py
│   ├── build_db.py
│   ├── build_morphology.py
│   ├── build_masadir_derivatives.py
│   ├── build_root_glosses.py
│   └── build_plain_columns.py
└── examples/
    ├── queries.sql
    └── masadir_queries.sql
```

---

## ⚙️ المتطلبات

| المكوّن | الإصدار | ملاحظة |
|---------|---------|--------|
| **Git + Git LFS** | حديث | لسحب `data/*.db` و `*.parquet` (114-169 MB لكل ملف) |
| **Python** | `>=3.11` (يفضّل `3.13` لـ `Django 6.1`) | للـ backend و سكربتات البناء |
| **Node.js** | `>=20` | للـ frontend (Next 16 يتطلب 18.17+، يفضّل 20) |
| **npm / pnpm / yarn** | `npm >=10` | `npm install` هو الموصى به هنا |
| **SQLite** | `>=3.35` | القاعدة جاهزة، لا تحتاج تثبيت إضافي |

> تحقق سريع:
> ```bash
> python3 --version
> node --version
> npm --version
> git lfs version
> ```

---

## 📥 الاستنساخ السريع

> **مهم:** استخدم `--depth 1` لتجنب تحميل كامل السجل (يوفّر ~800 MB من `.git` history). البيانات الكبيرة تُسحب عبر `Git LFS`.

```bash
git clone --depth 1 https://github.com/AhmedSaadi0/quran-words.git
cd quran-words

git lfs pull

ls -lh data/quran_words.db
ls -lh data/arabic_roots.json
```

> **بدون Git LFS** سترى ملفات pointer صغيرة (134 byte). إن حدث ذلك شغّل `git lfs install && git lfs pull`.

> **لتحديث لاحقاً بعد --depth 1:**
> ```bash
> git pull --depth 1
> git lfs pull
> ```

---

## 🚀 البدء السريع — بدون بناء

استخدم القاعدة الجاهزة مباشرة (لا حاجة لإعادة البناء):

```bash
sqlite3 data/quran_words.db
sqlite> SELECT * FROM masadir WHERE root='كتب' LIMIT 5;
sqlite> SELECT * FROM derivatives WHERE root='علم' AND is_quranic=1;
sqlite> .quit

python3 -c "
import sqlite3
conn = sqlite3.connect('data/quran_words.db')
print(conn.execute(\"SELECT masdar_plain FROM masadir WHERE root='رحم' LIMIT 3\").fetchall())
"
```

```python
import sqlite3
conn = sqlite3.connect("data/quran_words.db")
conn.execute("SELECT masdar_plain FROM masadir WHERE root='رحم'").fetchall()
```

---

## 🖥️ تشغيل الخلفية — Django + DRF

الخلفية تقرأ `data/quran_words.db` مباشرة كـ `managed=False` (لا إعادة إنشاء) عبر `backend/config/settings.py:64`.

### 1) إنشاء البيئة الافتراضية

```bash
python3 -m venv backend/.venv

source backend/.venv/bin/activate
```

### 2) تثبيت المتطلبات

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 3) تهيئة قاعدة البيانات (جداول auth فقط)

```bash
python backend/manage.py migrate --run-syncdb
```

> `backend/config/settings.py:64` يشير إلى `BASE_DIR.parent / "data" / "quran_words.db"` مع `timeout: 20`.
> `CORS_ALLOW_ALL_ORIGINS = True` و `ALLOWED_HOSTS = ["*"]` للتطوير (قيّده في الإنتاج).

### 4) تشغيل الخادم

```bash
python backend/manage.py runserver 0.0.0.0:8000 --noreload
```

افتح في المتصفح أو عبر `curl`:

```bash
curl http://127.0.0.1:8000/api/stats/ | jq

curl "http://127.0.0.1:8000/api/search/?q=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/masadir/?root=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/words/1/detail/" | jq
```

المتصفح: `http://127.0.0.1:8000/api/` — واجهة DRF القابلة للتصفح.

### 5) الإنتاج (اختياري)

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
backend/.venv/bin/gunicorn config.wsgi:application --chdir backend --bind 0.0.0.0:8000
```

### 6) الاختبار

```bash
backend/.venv/bin/python backend/scripts/smoke_api.py --base http://127.0.0.1:8000/api

backend/.venv/bin/python backend/scripts/smoke_api.py --base http://127.0.0.1:8765/api \
    --save /tmp/opencode/after --compare /tmp/opencode/baseline
```

> **ملاحظة جانغو 6.1:** يتطلب `Python 3.13` في البيئة الحالية (`IMPLEMENTATION_PLAN.md`). إن كنت على `3.11/3.12` ثبّت `Django 5.x` أو حدّث بايثون.

---

## 🌐 تشغيل الواجهة — Next.js

الواجهة مبنية بـ **Next.js 16 + Tailwind 4 + RTL كامل + خط Amiri** (`frontend/src/app/layout.tsx`).

### 1) التثبيت

```bash
cd frontend

npm install

ls node_modules/.bin/next
```

> **ملاحظة `vendor/`:** مجلد `frontend/vendor/` يحوي `next-16.3.2.tgz` و `swc` و `sharp` tarballs لتجاوز الشبكة البطيئة. على شبكة جيدة يمكنك حذف `vendor/` وإرجاع `"next": "16.3.2"` في `package.json`.

### 2) إعداد متغير البيئة (اختياري)

الواجهة تتصل بالخلفية عبر `frontend/src/lib/api.ts:6`:

```ts
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
```

```bash
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api' > .env.local
echo 'NEXT_PUBLIC_API_URL=https://api.example.com/api' > .env.local
```

### 3) تشغيل خادم التطوير

```bash
npm run dev
```

افتح `http://localhost:3000` — يجب أن ترى:
* شريط بحث كبير (`ابحث بجذر: كتب / بمصدر: كتابة / بكلمة: عَلِيم`)
* 6 بطاقات إحصائيات من `/api/stats/`
* شبكة جذور (20/صفحة)

### 4) أوامر إضافية

```bash
npm run build
npm start
npm run lint
```

> **ملاحظة Next 16:** `params` و `searchParams` هما `Promise` → `await props.params` في `page.tsx`.

---

## 🔗 التشغيل المتكامل — الخلفية + الواجهة

تحتاج نافذتين (terminal):

```bash
source backend/.venv/bin/activate
python backend/manage.py runserver 0.0.0.0:8000 --noreload

cd frontend
npm run dev
```

| الخدمة | الرابط الافتراضي | الصحة |
|--------|------------------|-------|
| **Django API** | `http://localhost:8000/api/` | `curl http://localhost:8000/api/stats/` |
| **Next.js Web** | `http://localhost:3000` | افتح المتصفح وابحث عن `كتب` |
| **DRF Browsable** | `http://localhost:8000/api/roots/?search=كتب` | واجهة تصفح JSON |

**تجربة سريعة متكاملة:**

1. افتح `http://localhost:3000`
2. ابحث عن `كتب` → سترى جذور/مصادر/كلمات من `GET /api/search/?q=كتب`
3. ادخل صفحة جذر `/roots/كتب` → تبويبات المعاني/المصادر/المشتقات
4. ادخل صفحة كلمة `/words/1` → تحليل صرفي + كل مواضعها
5. ادخل صفحة سورة `/surahs/1` → عرض مصحفي مع `hover` للتحليل

> إن فشل الاتصال، تأكد أن `NEXT_PUBLIC_API_URL` يشير إلى المنفذ الصحيح وأن الباكند يعمل على `8000`.

---

## 🏗️ بناء القاعدة من الصفر (3 مراحل)

> تخطَّ هذا القسم إن كنت تستخدم `data/quran_words.db` الجاهزة (114 MB). للبناء الكامل تحتاج ~**50 MB** إضافية لـ CAMeL + ~**250 MB** بيانات خام.

```bash
python --version
pip install --user camel-tools pyarrow
camel_data -i morphology-db-msa-r13

python scripts/download_quran.py
python scripts/fetch_corpus.py
python scripts/fetch_arabic_roots.py

python scripts/build_db.py
python scripts/build_morphology.py

python scripts/build_masadir_derivatives.py

python scripts/build_root_glosses.py
python scripts/build_plain_columns.py
```

> **ملاحظة الحجم:** `camel-tools` نفسها 0.12MB لكنها تتطلب `scikit-learn`/`camel-kenlm` (~12MB) + قاعدة `calima-msa-r13` (~40MB). `torch` (526MB) مطلوب فقط لنموذج `BERT` السياقي وغير لازم لهذا السكربت.

> **Git LFS:** بعد البناء، الملفات الكبيرة (`*.db`, `*.parquet`) تُتعقّب عبر `data/** filter=lfs` في `.gitattributes`. لا تُحمّلها مباشرة في `git` بدون LFS.

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

## 🔌 واجهة البرمجة API

الخلفية تكشف **15 endpoint** عبر `backend/config/urls.py:4` → `api/` (انظر `backend/README.md` للتفصيل الكامل).

| المسار | الوصف | مثال |
|--------|-------|------|
| `GET /api/stats/` | إحصائيات عامة | `curl /api/stats/` |
| `GET /api/search/?q=كتب&type=all` | بحث موحد (جذر>مصدر>كلمة). `type=root\|masdar\|word\|all` | `?q=كتب&type=root` |
| `GET /api/roots/?search=كتب` | جذور (20/صفحة) | `?search=رحم` |
| `GET /api/roots/{id}/` | تفاصيل جذر | `/api/roots/19/` |
| `GET /api/masadir/?root=كتب` | مصادر جذر | `?root=كتب` |
| `GET /api/derivatives/?root=علم&is_quranic=1` | مشتقات | `?root=علم&is_quranic=1` |
| `GET /api/meanings/?root_id=19` | معاني (filter بـ `root_id`) | `?root_id=19` |
| `GET /api/words/?search=رحمن` | كلمات (بحث بدون تشكيل) | `?search=الرحمن` |
| `GET /api/words/{id}/detail/` | كلمة + كل مواضعها + مصدرها + مشتقاتها | `/api/words/1/detail/` |
| `GET /api/surahs/` | 114 سورة | |
| `GET /api/ayat/?surah=1` | آيات سورة | `?surah=1` |
| `GET /api/ayah-words/?surah=1` | آيات مع كلماتها وتحليلها (للصفحة المصحفية) | `?surah=1&page_size=50` |
| `GET /api/morphology/` | تحليلات صرفية خام | `?pos=N&root=كتب` |
| `GET /api/lemmas/` | الأصول | |
| `GET /api/sources/` | مصادر البيانات والتراخيص | |

> **المعنى السريع:** كل استجابات الجذور (قائمة/تفصيل/بحث) وكائن `root` في تفاصيل الكلمة تتضمن `gloss_ar/gloss_en/gloss_source` — مختصراً من جدول `root_glosses` (يُبنى بـ `python scripts/build_root_glosses.py`).

> **تطبيع البحث:** `backend/core/utils.py:strip_diacritics` + `normalize_ar` يطبّع `ٱلرَّحْمـٰنِ` ↔ `الرحمن` في الخلفية والواجهة (`frontend/src/lib/normalize.ts` نسخة JS مطابقة).

### أمثلة curl (مُرمّزة)

```bash
curl "http://127.0.0.1:8000/api/search/?q=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/masadir/?root=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/words/1/detail/" | jq
curl "http://127.0.0.1:8000/api/surahs/1" | jq
curl "http://127.0.0.1:8000/api/ayah-words/?surah=1&page_size=2" | jq
```

انظر `backend/README.md:88-100` لهيكلة الـ Apps الثمانية.

---

## 🔍 أمثلة على الاستعلامات

### أساسي
```sql
SELECT a.ayah, wa.position, w.text, wm.pos, r.root, wm.form
FROM word_ayah wa
JOIN words w ON wa.word_id=w.id
JOIN ayat a ON wa.ayah_id=a.id
LEFT JOIN word_morphology wm ON wm.word_ayah_id=wa.id
LEFT JOIN roots r ON r.id=wm.root_id
WHERE a.surah=1 ORDER BY a.ayah, wa.position;

SELECT rm.book_name, rm.definition FROM roots r
JOIN root_meanings rm ON rm.root_id=r.id WHERE r.root='رحم' LIMIT 3;
```

### مصادر ومشتقات (جديد)
```sql
SELECT masdar_ar, pattern, form, is_attested, source
FROM masadir WHERE root='كتب' ORDER BY is_attested DESC, confidence DESC;

SELECT form_ar, derivative_type, pattern FROM derivatives
WHERE root='علم' AND is_quranic=1;

SELECT w.text, r.root, m.masdar_plain, m.pattern
FROM word_ayah wa
JOIN words w ON wa.word_id=w.id
JOIN word_morphology wm ON wm.word_ayah_id=wa.id
JOIN roots r ON r.id=wm.root_id
JOIN masadir m ON m.root_id=r.id
WHERE wa.ayah_id=1 GROUP BY wa.id LIMIT 5;

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

## ❓ استكشاف الأخطاء

| المشكلة | الحل |
|---------|------|
| `data/quran_words.db` حجمه 134 byte | لم يُسحب LFS. شغّل `git lfs install && git lfs pull` |
| `port 8000 already in use` | `lsof -i :8000` ثم `kill` أو غيّر المنفذ `runserver 0.0.0.0:8001` وحدّث `NEXT_PUBLIC_API_URL` |
| `port 3000 already in use` | `lsof -i :3000` أو `npm run dev -- -p 3001` |
| `ModuleNotFoundError: No module named 'rest_framework'` | تأكد من تفعيل `.venv` و `pip install -r backend/requirements.txt` داخلها |
| `next: not found` بعد `npm install` | احذف `node_modules` و `package-lock.json` ثم `npm install` مجدداً (يقرأ `vendor/next-16.3.2.tgz`) |
| `autoreload` ينهار / `RuntimeError` | استخدم `--noreload` كما في `backend/README.md:16` |
| `CORS error` في المتصفح | تأكد أن الباكند يعمل وأن `CORS_ALLOW_ALL_ORIGINS=True` في `backend/config/settings.py:75` |
| `404 /api/...` | تأكد أن الطلب يبدأ بـ `/api/` (مُعرّف في `backend/config/urls.py:16`) |
| `npm install` بطيء جداً | طبيعي مع `vendor/` — `frontend/.npmrc:1` يضبط `fetch-timeout=600000` |
| `git clone` بطيء / كبير | استخدم `git clone --depth 1` كما في [الاستنساخ السريع](#-الاستنساخ-السريع) |

---

## 🤝 المساهمة

مرحباً بالمساهمات:
- إضافة ترجمات بلغات أخرى
- تحسين قوائم الأوزان (`MASDAR_PATTERNS_BY_FORM` في `build_masadir_derivatives.py`)
- إضافة معاجم جديدة
- إصلاح التشكيل للمصادر
- تحسين واجهة Next.js (مكونات `src/components/`)

```bash
git clone --depth 1 https://github.com/AhmedSaadi0/quran-words.git
cd quran-words
```

---

## 📄 الترخيص

كود المشروع: **MIT** ([LICENSE](LICENSE)).
البيانات: انظر الجدول أعلاه (CC-BY-4.0 / GPL / GPL-3.0 / MIT).

---

## 🙏 الشكر

[Quran.com](https://quran.com) و [Quranic Arabic Corpus](http://corpus.quran.com) و [Hawramani](http://arabiclexicon.hawramani.com) و [CAMeL Lab - NYU Abu Dhabi](https://github.com/CAMeL-Lab/CAMeL_Tools) على البيانات المفتوحة.
