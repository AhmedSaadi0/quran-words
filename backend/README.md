# Quran Words — Backend (Django + DRF)

واجهة برمجية لتصفح 77,429 موضع كلمة مع جذورها (1,642) ومصادرها (5,273) ومشتقاتها (16,245) — مبنية على `data/quran_words.db`.

## التشغيل السريع

```bash
# من جذر المشروع quran-words/
python3.13 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate --run-syncdb  # ينشئ auth tables فقط
backend/.venv/bin/python backend/manage.py runserver 0.0.0.0:8000 --noreload
# افتح http://127.0.0.1:8000/api/stats/
```

> **ملاحظة:** استخدم `--noreload` في التطوير بسبب تضارب `autoreload` مع `models` غير المُدارة. في الإنتاج استخدم `gunicorn`.

## المتطلبات

* Python >=3.11
* `pip install Django==6.1 djangorestframework==3.18.0 django-filter==26.1 django-cors-headers==4.9.0`
* لا يحتاج `torch` — البحث يعمل بـ `SQLite` فقط.

## الإعداد

`backend/config/settings.py` يشير مباشرة إلى `../data/quran_words.db` (read-only mount في Docker). لا حاجة لـ `makemigrations` لجداول القرآن (`managed=False`).

```python
DATABASES = {
  "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR.parent / "data" / "quran_words.db"}
}
CORS_ALLOW_ALL_ORIGINS = True  # قيّده في الإنتاج
```

## نقاط API

| المسار | الوصف |
|--------|-------|
| `GET /api/stats/` | إحصائيات عامة |
| `GET /api/search/?q=كتب&type=all` | بحث موحد (جذر>مصدر>كلمة). `type=root\|masdar\|word\|all` |
| `GET /api/roots/?search=كتب` | جذور (20/صفحة) |
| `GET /api/roots/{id}/` | تفاصيل جذر |
| `GET /api/masadir/?root=كتب` | مصادر جذر |
| `GET /api/derivatives/?root=علم&is_quranic=1` | مشتقات |
| `GET /api/meanings/?root_id=19` | معاني (filter بـ `root_id` integer) |
| `GET /api/words/?search=رحمن` | كلمات (بحث بدون تشكيل) |
| `GET /api/words/{id}/detail/` | كلمة + كل مواضعها + مصدرها + مشتقاتها |
| `GET /api/surahs/` | 114 سورة |
| `GET /api/ayat/?surah=1` | آيات سورة |
| `GET /api/ayah-words/?surah=1` | آيات مع كلماتها وتحليلها (للصفحة المصحفية) |
| `GET /api/morphology/` | تحليلات صرفية خام (فلترة بـ `pos` و `root`) |
| `GET /api/sources/` | مصادر البيانات والتراخيص |

> **المعنى السريع:** كل استجابات الجذور (قائمة/تفصيل/بحث) وكائن `root` في تفاصيل الكلمة
> تتضمن `gloss_ar/gloss_en/gloss_source` — مختصراً من جدول `root_glosses`
> (يُبنى بـ `python scripts/build_root_glosses.py` — تغطية 95% عربي، 76% إنجليزي).

### أمثلة curl (مُرمّزة)

```bash
curl "http://127.0.0.1:8000/api/search/?q=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/masadir/?root=%D9%83%D8%AA%D8%A8" | jq
curl "http://127.0.0.1:8000/api/words/1/detail/" | jq
curl "http://127.0.0.1:8000/api/surahs/1" | jq
```

> **تطبيع البحث:** `core/utils.py:strip_diacritics` + `normalize_ar` يطبّع `ٱلرَّحْمـٰنِ` ↔ `الرحمن` في الخلفية والواجهة.

## الإنتاج

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 60
```

`docker-compose` مقترح في `WEBSITE_PLAN.md:6`.

## الاختبار

```bash
# مع تشغيل السيرفر:
backend/.venv/bin/python backend/scripts/smoke_api.py --base http://127.0.0.1:8000/api
# مقارنة استجابات مع نسخة محفوظة (parity check):
backend/.venv/bin/python backend/scripts/smoke_api.py --base http://127.0.0.1:8765/api \
    --save /tmp/opencode/after --compare /tmp/opencode/baseline
```

## هيكلة الـ Apps

| App | المسؤولية |
|-----|-----------|
| `config/` | إعدادات المشروع وروابطه |
| `core/` | مشترك: تطبيع عربي + pagination |
| `quran/` | السور والآيات (`surahs`, `ayat`, `ayah-words`) |
| `words/` | الكلمات ومواضعها (`words`, `word-ayah`, `words/{id}/detail/`) |
| `morphology/` | التحليل الصرفي واللمات (`lemmas`, `morphology`) |
| `roots/` | الجذور ومعانيها (`roots`, `meanings`) |
| `derivatives/` | المصادر والمشتقات (`masadir`, `derivatives`) |
| `sources/` | مصادر البيانات (`sources`) |
| `search/` | البحث الموحد والإحصائيات (`search/`, `stats/`) |

## ملاحظات

* الجداول `managed=False` — لا تشغّل `migrate` لتعديلها.
* البحث الحالي `icontains` + تطبيع؛ لاحقاً أضف `FTS5` أو هاجر إلى `Postgres + pg_trgm`.
* `WordMasdar` يربط كل موضع بمصدرين أولين لتجنب الانفجار (66k رابط).
