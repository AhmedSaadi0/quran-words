# خطة موقع تصفح كلمات القرآن — Django + DRF + Next.js

> **الحالة:** خطة معتمدة — لم يبدأ التنفيذ بعد  
> **الأولوية:** البحث بالجذر والمصدر أولاً  
> **التقنية المختارة:** `Django + Django REST Framework` (Backend) + `Next.js` (Frontend)  
> **الاستضافة:** لم تُحدد بعد — موصى به VPS (انظر §6)

---

## 1) الوضع الحالي

### ما تملكه الآن (مُتحقق من الملفات)

* `data/quran_words.db` (107 MB) — 12 جدولاً فعالاً:

| الجدول | العدد |
|--------|-------|
| `surahs` | 114 |
| `ayat` | 6,236 |
| `words` | 21,295 كلمة فريدة |
| `word_ayah` | 77,429 موضع |
| `roots` | 1,642 جذر مدقق (QAC) |
| `lemmas` | 4,832 |
| `word_morphology` | 77,429 تحليل لكل موضع |
| `root_meanings` | 9,639 |
| `masadir` | 5,273 مصدر (جديد) |
| `derivatives` | 16,245 مشتق (جديد) |
| `word_masdar` | 66,436 رابط كلمة←مصدر |

* الجذور والمصادر والمشتقات مبنية بالفعل عبر:
  * `scripts/build_masadir_derivatives.py:260` (جداول `masadir`, `derivatives`, `word_masdar`)
  * `data/quranic_corpus_morphology.json` (42 MB) + `arabic_roots.json` (162 MB)
  * تحقق صرفي بـ `CAMeL Tools + CALIMA-Star` (`~/.camel_tools/data/morphology_db/calima-msa-r13/morphology.db`)

* لا يوجد واجهة ويب حالياً — فقط:
  * `README.md` (320 سطر)
  * `examples/queries.sql` و `examples/masadir_queries.sql`

### لماذا ليس Farasa؟

تم تقييمها واستُبعدت: `QAC` تدقيق بشري أدق على الرسم العثماني، و`Farasa` لا تولّد قائمة مصادر/مشتقات. الاختيار وقع على `CAMeL Tools` (MIT، توليد صرفي حقيقي).

---

## 2) القرارات المعمارية

### 2.1 نظرة عامة

```
[ المتصفح ] --HTTPS--> [ Nginx ] --/api/*--> [ Django + DRF + SQLite (107MB) ]
                      \--/*----> [ Next.js SSR ]
```

* **الخلفية:** `Django` يقرأ `quran_words.db` كـ `managed=False` عبر `inspectdb` (لا إعادة إنشاء). لاحقاً يمكن الهجرة إلى `Postgres` إذا احتاج البحث العربي `pg_trgm`.
* **الواجهة:** `Next.js App Router + TypeScript + Tailwind + RTL`. `SSR` لصفحات السور/الكلمات لأغراض `SEO`. بحث فوري `debounced 300ms`.
* **مرفوض:** `SQLite-WASM` في المتصفح — `107MB` ثقيل على التحميل الأول.

### 2.2 هيكل المجلدات المقترح

```
quran-words/
├── backend/
│   ├── quran/                  # Django project
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── words/                  # App رئيسي
│   │   ├── models.py           # Surah, Ayah, Word, WordAyah, Root, Lemma, Morphology, Masdar, Derivative
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── search.py           # FTS5 + تطبيع تشكيل
│   ├── api/                    # DRF routers
│   └── data -> ../data/quran_words.db (read-only mount)
├── frontend/
│   ├── app/
│   │   ├── page.tsx                    # الرئيسية: بحث + شبكة جذور
│   │   ├── search/page.tsx             # نتائج بحث متقدم
│   │   ├── roots/[root]/page.tsx       # صفحة جذر
│   │   ├── words/[id]/page.tsx         # صفحة كلمة
│   │   └── surahs/[id]/page.tsx        # تصفح مصحفي
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── WordCard.tsx
│   │   ├── RootBadge.tsx
│   │   ├── MasdarList.tsx
│   │   └── DerivativeGrid.tsx
│   └── lib/
│       ├── api.ts
│       └── normalize.ts        # strip_diacritics مطابق للباك
├── examples/                   # موجود
├── data/                       # موجود
└── docker-compose.yml
```

---

## 3) تصميم قاعدة البيانات للويب

* **لا تغيير في البيانات** — فقط فهارس للبحث:

```sql
-- للبحث السريع بالجذر/المصدر/الكلمة
CREATE VIRTUAL TABLE search_fts USING fts5(
  root, masdar_plain, derivative_plain, word_clean,
  content='', tokenize='unicode61 "remove_diacritics 1"'
);
-- أو Postgres: CREATE EXTENSION pg_trgm; CREATE INDEX ON words USING gin (text_clean gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_masadir_plain ON masadir(masdar_plain);
CREATE INDEX IF NOT EXISTS idx_derivatives_plain ON derivatives(form_plain);
CREATE INDEX IF NOT EXISTS idx_words_clean ON words(text_clean);
```

* **التطبيع الموحد:** `strip_diacritics` (`scripts/build_masadir_derivatives.py:78`) + `normalize_root` (إزالة `ٱ`، `ـ`، توحيد الهمزات) يُستخدم في `backend/search.py` و `frontend/lib/normalize.ts` لضمان تطابق `ٱلرَّحْمـٰنِ` ↔ `الرحمن`.

---

## 4) واجهة برمجة التطبيقات (DRF) — 8 نقاط

| المسار | الوصف | مثال |
|--------|-------|------|
| `GET /api/search/?q=&type=` | بحث موحد (weight: root>masdar>word). `type=root\|masdar\|plain\|translation` | `?q=كتب&type=root` → `كتب` + مصادره |
| `GET /api/roots/?q=&page=` | قائمة جذور (20/صفحة) | `?q=رحم` |
| `GET /api/roots/{id}/` | تفاصيل جذر |  |
| `GET /api/roots/{id}/masadir` | مصادر الجذر |  |
| `GET /api/roots/{id}/derivatives?is_quranic=1` | مشتقات الجذر |  |
| `GET /api/roots/{id}/meanings` | معاني من `root_meanings` |  |
| `GET /api/words/?root=&masdar=&surah=&pos=` | فلترة كلمات | `?root=كتب&masdar=كتابة` |
| `GET /api/words/{id}/` | كلمة مع `morphology`, `segments` JSON, `masadir` عبر `word_masdar` |  |
| `GET /api/surahs/` | 114 سورة |  |
| `GET /api/surahs/{id}/ayat` | آيات سورة |  |
| `GET /api/ayat/{id}/words` | كلمات آية مع تحليل |  |
| `GET /api/stats/` | إحصائيات للهيرو |  |

* ترقيم: `PageNumberPagination(20)`
* تخزين مؤقت: `Cache-Control: public, max-age=3600` للجذور الثابتة
* تحديد معدل: `100/min` لكل `IP`

**منطق البحث (الجذر/المصدر أولاً):**
1. طبّع `q` (أزل تشكيل).
2. ابحث في `roots.root` ثم `masadir.masdar_plain` ثم `derivatives.form_plain` ثم `words.text_clean`.
3. أرجع `roots` أولاً مع `badge` (ذهب للقرآني `is_attested`), ثم `masadir` قابلة للنقر لفلترة `words`.

---

## 5) واجهة Next.js — الصفحات والمكونات

### 5.1 الصفحات

* **`/` (الرئيسية):** شريط بحث كبير (`placeholder: "ابحث بجذر: كتب / بمصدر: كتابة / بكلمة: عَلِيم"`), تبويبا `جذور`/`مصادر` في الأعلى, شبكة `1,642` جذر (افتراضياً الأكثر وروداً), بطاقات إحصائيات.
* **`/search?q=رحم`:** نتائج مجمعة: قسم `جذور` → `مصادر` → `كلمات` → `آيات`. فلتر جانبي `قرآني فقط / CAMeL`.
* **`/roots/[root]` (مثلاً `/roots/كتب`):**
  * هيدر: `كتب` + عدد الكلمات
  * تبويب `المعاني` من `root_meanings` (الراغب، لسان العرب...)
  * قائمة `مصادر` مع `pattern` (`فَعَالة، افتعال`) وشارة ذهبية لـ `is_attested`
  * شبكة `مشتقات` مع فلتر `قرآني فقط`, كل بطاقة تظهر `form_ar` + `derivative_type` + إن وجدت كلمة قرآنية
  * جدول `كلمات الجذر` (مرقم) + خريطة توزع سور
* **`/words/[id]` (مثلاً `/words/123`):**
  * `ٱلرَّحْمـٰنِ` + `transliteration` + `translation`
  * `pos/form/case/state/derivation` + `segments` مرسومة بصرياً
  * `مصدر` الكلمة + `كل مشتقات جذرها` (قابلة للنقر)
  * `كل آياتها` مع `text_uthmani` وزر نسخ/تشغيل
* **`/surahs/[id]`:** عرض مصحفي `text_uthmani` مع `hover` يظهر تحليل كل كلمة (tooltip). تنقل `جزء/حزب`.

### 5.2 المكونات

* `SearchBar.tsx` — `debounced`, تطبيع تشكيل في الواجهة قبل الإرسال
* `WordCard.tsx`, `RootBadge.tsx`, `MasdarList.tsx`, `DerivativeGrid.tsx`, `AyahView.tsx`, `MorphTooltip.tsx`

### 5.3 تجربة المستخدم

* `RTL` كامل، خط `Amiri` للنصوص و `Uthmanic` للآيات
* إظهار التشكيل في النتائج لكن تجاهله في الإدخال
* `SEO`: `SSR` لكل `surah/ayah/word/root` + `sitemap.xml` (114 + 6236 + 21295)

---

## 6) الاستضافة والنشر

* **موصى به (مرحلياً):** `VPS 2GB` (Hetzner/DigitalOcean ~5$/شهر) + `Docker Compose` (خدمتان: `backend:gunicorn`, `frontend:node`, `nginx` كـ reverse proxy). أرخص ويحمل `107MB` بدون قيود.
* **بديل:** `Frontend على Vercel` (مجاني، SSR سريع) + `Backend على VPS` — يبقي `Next` سريعاً مع إبقاء `SQLite` محلياً.
* **مرفوض:** `GitHub Pages` — لا يشغّل `DRF`.
* **لاحقاً:** هجرة `SQLite → Postgres` مع `pg_trgm + unaccent` إذا زاد الضغط، أو `Cloudflare R2` للـ `parquet`.

**`docker-compose.yml` مقترح:**

```yaml
services:
  backend:
    build: ./backend
    volumes: [./data/quran_words.db:/app/data/quran_words.db:ro]
    command: gunicorn quran.wsgi:application --bind 0.0.0.0:8000
  frontend:
    build: ./frontend
    environment: [NEXT_PUBLIC_API_URL=https://api.example.com]
    ports: ["3000:3000"]
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: [./nginx.conf:/etc/nginx/nginx.conf]
```

---

## 7) مراحل التنفيذ

| المرحلة | المدة | المخرجات |
|---------|-------|----------|
| **M1 — Backend** | 3-4 أيام | `inspectdb` + `serializers` + `FTS5` + 8 endpoints + اختبارات على `masadir_queries.sql` + `sources` |
| **M2 — Frontend** | 5-6 أيام | إعداد Next + 4 صفحات + `SearchBar` مع تطبيع + ربط API |
| **M3 — بحث الجذر/المصدر** | 2 أيام | أوزان `FTS5`, `autocomplete` من `roots` + `masadir.masdar_plain`, فلترة متقدمة |
| **M4 — نشر** | 1-2 أيام | `Docker` + `nginx` + `SEO/sitemap` + صفحة `/sources` (ذكر GPL) |

---

## 8) مخاطر واحتياطات

| الخطر | التخفيف |
|-------|---------|
| `107MB` + `FTS5` ثقيل | لا ترسل `DB` للمتصفح؛ `LIMIT 20` + `defer` لحقل `segments` JSON |
| التشكيل العربي | طبّع في `backend` و `frontend` بنفس الدالة |
| `GPL` (QAC/Hawramani) | صفحة `/sources` تذكر `sources:4` مع روابط، وتوفير الكود المصدري |
| ضعف الجذور (و/ي/ء) | السكربت الحالي يقلل الضجيج عبر `is_weak_root` + `camel_valid` |

---

## 9) ما بعد الإطلاق (اختياري)

* تسجيل صوتي لكل كلمة، مقارنة ترجمات، تصدير `CSV/JSON` لنتائج البحث، `PWA` للعمل دون اتصال، لوحة تحكم لإضافة معاجم جديدة.

---

## 10) قرارات تحتاج تأكيدك قبل البدء

1. هل نبدأ بـ `VPS` أم تفضل `Vercel Frontend + VPS Backend`؟
2. هل تريد هجرة فورية إلى `Postgres` أم نبدأ بـ `SQLite` ثم نهاجر؟
3. هل تريد إضافة تسجيل دخول/مفضلة لاحقاً أم الاكتفاء بالتصفح المفتوح؟

> عند الموافقة، سيُنشأ `backend/` و `frontend/` مع `Docker` ويُربط `quran_words.db` مباشرة.
