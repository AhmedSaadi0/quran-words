# خطة التنفيذ — إعادة هيكلة الباكند + بناء الفرونت اند

> **الحالة:** ✅ مكتملة (2026-08-23)
> **المرجع:** `WEBSITE_PLAN.md` (الخطة المعتمدة الأصلية)
> **عقد ثابت:** مسارات الـ API تبقى كما هي حرفياً — أي تغيير مستقبلي يمر عبر هذه الخطة

---

## الإضافة اللاحقة: المعنى السريع الشامل (root_glosses) ✓

- `scripts/build_root_glosses.py`: يستخرج معنى مختصراً (سطر/سطران) لكل جذر من 8 قواميس
  - عربي: الراغب ← ابن سيده ← الجوهري ← الزمخشري ← العين ← لسان العرب ← تاج العروس (fallback تلقائي، رفض الآيات/الشواهد/تعداد الحروف/الإسنادات النحوية) — تغطية **95%**
  - إنجليزي: أول جملة من معجم لين — تغطية **76%**
- جدول جديد `root_glosses` في نفس DB (إضافة آمنة فقط، managed=False)
- API: حقول `gloss_ar/gloss_en/gloss_source` في كل استجابات الجذور (قائمة/تفصيل/بحث) + داخل كائن `root` في `/api words/{id}/detail/` + حقل `root_gloss` داخل تحليل ayah-words
- الفرونت: بطاقة «المعنى المختصر» أعلى تبويبات صفحة الجذر + سطر «المعنى السريع للجذر» في صفحة الكلمة + سطر المعنى في بطاقات الجذور (الرئيسية والبحث) + سطر المعنى في popover السورة

---

## الإضافة: تحسينات الجولة الثالثة ✓

### 1) بحث الكلمات والآيات بالنص العادي — أُصلح
- `scripts/build_plain_columns.py`: عمودا `words.text_plain` و `ayat.text_uthmani_plain` مطبّعان بنفس دالة التطبيع
- البحث الآن: «الله» تجد «ٱللَّهِ»، و«كتاب» تجد «ٱلْكِتَـٰبُ» — في unified_search وwords

### 2) دليل المصطلحات الصرفية — جديد
- `lib/morphology.ts`: مصدر وحيد للحقيقة — 59 مصطلحاً بتسمية عربية + شرح موجز + شرح مفصل + مثال قرآني
- صفحات: `/guide/morphology` (فهرس) و `/guide/morphology/[term]` — 58 صفحة SSG للـ SEO
- قيم جدول التحليل الصرفي (صفحة الكلمة) وقيم popover السورة أصبحت روابط منقطة للدليل
- القيم المبنية على جرد فعلي لقيم DB (33 pos، 11 form، MS/FP…، special: إنّ/كان/كاد)

### baseline محفوظة v3 بعد توسّع استجابة ayah-words بحقل root_gloss

---

## نتائج التنفيذ

### المرحلة A — الباكند ✓
- هيكلة جديدة: `config/ core/ quran/ words/ morphology/ roots/ derivatives/ sources/ search/`
- استجابات الـ 15 endpoint **مطابقة 100%** للـ baseline قبل الهيكلة (`backend/scripts/smoke_api.py`)
- venv معزول: `backend/.venv` (python3.13)
- إصلاحات الجودة: except صريحة، إزالة N+1 في البحث، تبسيط فلتر الجذر، endpoints جديدة `/api/morphology/` و `/api/sources/`

### المرحلة B — الفرونت اند ✓
- Next.js 16 + Tailwind 4 + مكونات بأسلوب shadcn/ui (يدوية بسبب CLI تفاعلي) + RTL كامل + خط Amiri
- الصفحات: `/` · `/search?q=` · `/roots/[root]` · `/words/[id]` · `/surahs/[id]` · `/sources`
- التجولة المتكاملة نجحت على كل المسارات

### قيود معروفة (من الخطة الأصلية)
- بحث الكلمات/الآيات بالنص العادي (`الله`) لا يطابق النص المشكول في DB (`ٱللَّهِ`) — الحل المستقبلي: أعمدة مطبعة أو FTS5. الجذور والمصادر والمشتقات تعمل بشكل كامل.
- `frontend/vendor/`: tarballs محلية لـ next/swc/sharp بسبب شبكة بطيئة جداً — على شبكة جيدة يمكن استرجاع `"next": "16.3.2"` في package.json وحذف vendor.

---

## المرحلة A — إعادة هيكلة الباكند

### A1. البيئة
- إنشاء `backend/.venv` بـ `python3.13` (Django 6.1 متاح له فقط حالياً)
- `pip install -r requirements.txt` داخل الـ venv
- توثيق أمر التشغيل في README

### A2. Baseline
- تشغيل السيرفر على منفذ ثابت (8765) وحفظ استجابات كل endpoint في `/tmp/opencode/baseline/`
- تُستخدم للمقارنة بعد الهيكلة لضمان عدم تغيّر العقد

### A3. التقسيم إلى Apps — كل app وظيفة واحدة

| App | المسؤولية | النماذج | الـ Views |
|-----|-----------|---------|-----------|
| `config/` | إعدادات المشروع وروابطه (بدل مجلد `quran/` القديم لتجنب التعارض) | — | — |
| `core/` | مشترك: التطبيع العربي + Pagination | — | — |
| `quran/` | النص القرآني: السور والآيات | `Surah`, `Ayah` | `surahs`, `ayat`, `ayah-words` |
| `words/` | الكلمات ومواضعها | `Word`, `WordAyah` | `words`, `word-ayah`, `words/{id}/detail/` |
| `morphology/` | التحليل الصرفي واللمات | `Lemma`, `WordMorphology` | `lemmas` |
| `roots/` | الجذور ومعانيها | `Root`, `RootMeaning` | `roots`, `meanings` |
| `derivatives/` | المصادر والمشتقات | `Masdar`, `Derivative`, `WordMasdar` | `masadir`, `derivatives` |
| `sources/` | مصادر البيانات (GPL attribution) | `Source`, `WordSource` | `sources` |
| `search/` | البحث الموحد والإحصائيات فقط | — | `search/`, `stats/` |

**قواعد الهيكلة:**
- كل الجداول `managed=False` مع `db_table` كما هي → صفر migrations، صفر خطر على البيانات
- FKs بين الـ apps بمراجع نصية: `FK("roots.Root")`, `FK("words.Word")`...
- كل app يحوي: `models.py`, `serializers.py`, `views.py`, `urls.py`, `apps.py`, `tests.py`

### A4. عقد الـ API (غير متغيّر)

| المسار | App |
|--------|-----|
| `GET /api/surahs/` | quran |
| `GET /api/ayat/` · `/api/ayah-words/?surah=` | quran |
| `GET /api/words/` · `/api/words/{id}/detail/` · `/api/word-ayah/` | words |
| `GET /api/lemmas/` · `/api/morphology/` | morphology |
| `GET /api/roots/` · `/api/meanings/` | roots |
| `GET /api/masadir/` · `/api/derivatives/` | derivatives |
| `GET /api/sources/` | sources |
| `GET /api/search/?q=&type=` · `/api/stats/` | search |

### A5. إصلاحات الجودة (داخل الهيكل الجديد)
1. استبدال `except:` العارية في `word_detail` باستعلامات `.first()` صريحة
2. إزالة N+1 في `unified_search`: استعلامان مجمعان بعدادات المصادر/المشتقات بدل استعلام لكل جذر
3. تبسيط منطق فلتر الجذر في `WordViewSet` (إزالة الاستعلام المزدوج)

### A6. التحقق
- `manage.py check`
- `backend/scripts/smoke_api.py`: يضرب كل endpoint ويحفظ النتائج، ثم مقارنة مع baseline (`diff`)

---

## المرحلة B — الفرونت اند (Next.js 16 + shadcn/ui)

### B1. الإعداد
- shadcn/ui init بثيم **neutral** محايد + مكونات: `button input card tabs badge skeleton select separator popover tooltip scroll-area`
- `<html lang="ar" dir="rtl">` + خط **Amiri** (`next/font/google`) للآيات والعناوين العربية
- `src/lib/api.ts`: عميل fetch مكتوب الأنواع + أنواع DRF `{count,next,previous,results}`
  - `API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"`
- `src/lib/normalize.ts`: نسخة JS مطابقة حرفياً لدالة `normalize_ar` في الباكند

### B2. الصفحات الخمس

| الصفحة | مصدر البيانات | المحتوى |
|--------|---------------|---------|
| `/` | `stats/` + `roots/?page=` | SearchBar كبير + 6 بطاقات إحصائيات + شبكة جذور |
| `/search?q=` | `search/?q=` | أقسام مجمعة: جذور ← مصادر ← مشتقات ← كلمات ← آيات |
| `/roots/[root]` | `roots/?q=` ثم masadir/derivatives/meanings/words | تبويبات: المعاني / المصادر (شارة `is_attested`) / المشتقات (فلتر قرآني) / الكلمات |
| `/words/[id]` | `words/{id}/detail/` | الكلمة بخط كبير + translit/translation + تحليل صرفي + segments + آيات الوردود |
| `/surahs/[id]` | `ayah-words/?surah=&page_size=50` | عرض مصحفي، hover/click على الكلمة يظهر Popover بالتحليل الصرفي |

### B3. المكونات
`site-header` · `search-bar` (debounce 300ms client-side → ينقل إلى `/search?q=`) · `stats-cards` · `root-card` · `masdar-list` · `derivative-grid` · `ayah-view` · `morph-tooltip` · `pagination-controls`

**ملاحظة Next 16:** `params` و `searchParams` Promises → `await props.params`

---

## المرحلة C — التحقق النهائي
1. `npm run lint && npm run build` في frontend
2. تشغيل الباكند + الفرونت معاً
3. تجولة: البحث عن `كتب` → صفحة جذر → صفحة كلمة → صفحة سورة، ومطابقة المحتوى المعروض مع API

---

## ملاحظات بيئية
- Django يعمل حالياً عبر بايثون النظام `/usr/bin/python3.13` (site-packages المستخدم) — الهدف venv معزول داخل backend
- لا commit إلا بطلب صريح من المستخدم
