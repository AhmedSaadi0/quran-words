# AGENT.md — Quran Words Backend (Django + DRF, Read-Only)

> **Subsystem:** Django 5/6 + Django REST Framework read-only API over the 114 MB SQLite Quran database.
>
> **This file is the backend-specific guide.** It defines the Django architecture, the thin ViewSet pattern, the filtering/normalization contract, the frozen API envelope, and the gradual migration plan. The **universal** engineering principles (Clean Code §18, Function Design §19, Code Quality §20) live in the root [`AGENT.md`](../AGENT.md) and apply unchanged to every Python file.
>
> **Source-of-truth documents:**

| Document | Path |
| --- | --- |
| Frozen contract (15 endpoints) | [`../IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md) §A4 |
| Architecture plan | [`../WEBSITE_PLAN.md`](../WEBSITE_PLAN.md) |
| Operational detail | [`README.md`](README.md) |
| Query ground truth | [`../examples/queries.sql`](../examples/queries.sql) |

> When this file conflicts with those, the frozen contract wins; when those are silent, this file is authoritative. Universal rules (§18-20) always win over subsystem rules.

---

## Table of Contents

0. [Golden Rule: Never Assume — Always Ask](#0-golden-rule-never-assume--always-ask)
1. [Architectural Invariants](#1-architectural-invariants)
2. [App Directory Structure](#2-app-directory-structure)
3. [Model Standards](#3-model-standards)
4. [Views, Filtering & Selectors (Optional)](#4-views-filtering--selectors-optional)
5. [DRF API Standards](#5-drf-api-standards)
6. [Filtering, Normalization & N+1 Prevention](#6-filtering-normalization--n1-prevention)
7. [URL Routing](#7-url-routing)
8. [Code Validation (Before Submitting)](#8-code-validation-before-submitting)
9. [Critical Constraints (Do Not Violate)](#9-critical-constraints-do-not-violate)
A. [Appendix A — Quick Reference Card](#appendix-a--quick-reference-card)

> **Universal principles (§18-20):** see [`../AGENT.md`](../AGENT.md). Clean Code, Function Design, and Code Quality apply unchanged to every Python file in this backend.

---

## 0. Golden Rule: Never Assume — Always Ask

Before writing **any** code for an app / module, you MUST have 100% clarity on its structure. If you do not know the exact answer to any of these questions, **STOP and ask the user** — never proceed on guesswork.

### Questions to resolve before starting

| # | Question | Possible Answers / Notes |
| --- | --- | --- |
| 1 | **Which app does this belong to?** | `core` / `quran` / `words` / `morphology` / `roots` / `derivatives` / `sources` / `search` |
| 2 | **Does it need DRF endpoints?** | Yes → `views.py` + `serializers.py` + `urls.py` / No → helper only |
| 3 | **Does it need write / business logic?** | No — this is a **read-only** backend. Writes only via offline `scripts/*.py`. If you think you need a write endpoint, ask first. |
| 4 | **Does it need complex read / data-fetching?** | Yes → extract to `selectors.py` if >50 lines, else keep `enrich_*` helpers in `views.py` / No |
| 5 | **Does it need background tasks?** | No — no Celery in this project. Batch jobs are `scripts/` invoked manually. |
| 6 | **Does it touch Arabic normalization or search?** | `core/utils.py:14` `normalize_ar` / `search/views.py:20` `unified_search` |
| 7 | **What URLs need routing?** | Exact `api/...` path in `config/urls.py:4` `api_patterns` — must match frozen contract |

### Resulting action

Once every question is answered, the app structure is fully determined — apply the **Flat App** pattern from [§2](#2-app-directory-structure) below.

**NEVER guess or assume. Always ask until every question is answered with certainty.**

---

## 1. Architectural Invariants

These rules are non-negotiable. If a task appears to violate one, stop and ask the user to confirm an explicit exception.

### 1.1 The "≤ 3 models per app" guideline (soft cap)

> **Every Django app contains ≤ 3 concrete models as a guideline.** When a fourth model would be needed, consider splitting the domain — but do not over-split a cohesive domain.

The 8 apps in this project average **~1.6 models per app** — well within the guideline:

| App | Models | Count |
| --- | --- | --- |
| `quran` | `Surah`, `Ayah` | 2 |
| `words` | `Word`, `WordAyah` | 2 |
| `morphology` | `Lemma`, `WordMorphology` | 2 |
| `roots` | `Root`, `RootMeaning`, `RootGloss`, `RootAiSummary` | 4 (cohesive — gloss/ai are 1:1 extensions of Root) |
| `derivatives` | `Masdar`, `Derivative`, `WordMasdar` | 3 |
| `sources` | `Source`, `WordSource` | 2 |
| `search` | — (no models, stateless views) | 0 |
| `core` | — (no models, shared utils) | 0 |

`roots` having 4 is an intentional, documented exception — `RootGloss` and `RootAiSummary` are `OneToOneField` extensions added safely via `CREATE TABLE IF NOT EXISTS` (see `ROOT_AI_SUMMARY_PLAN.md:89`), not a new domain.

**Rule:** Prefer cohesion over rigid counting. If a new domain has >3 unrelated models, create a new app; if it is a 1:1 extension of an existing root entity, keep it in the same app.

### 1.2 No multi-tenancy, no auth (read-only public API)

- One SQLite database file, default schema: `BASE_DIR.parent / "data" / "quran_words.db"` (`config/settings.py:68`).
- No `django-tenants`, no `SHARED_APPS`, no JWT, no `django-guardian`.
- No authentication on any endpoint — all `GET` routes are public. Browsable API at `/api/` is intentional for exploration.
- Settings module is a single `config.settings` (no `base`/`dev`/`prod` split yet — add only if needed and ask first).
- `CORS_ALLOW_ALL_ORIGINS = True` and `ALLOWED_HOSTS = ["*"]` are dev-open; restrict in production via env (see §9).

### 1.3 Package dependency graph (no reverse edges)

```
                    ┌──────────┐
                    │   core   │  (normalize_ar, pagination, future renderers)
                    └────┬─────┘
                         │ depended on by everyone
         ┌───────────────┼───────────────┬──────────────┐
         ▼               ▼               ▼              ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  quran  │   │  words   │   │morphology│   │  roots   │
    └────┬────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
         │             │              │               │
         └──────┬──────┴──────┬───────┴──────┬────────┘
                ▼             ▼              ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │derivatives│  │ sources  │  │  search  │  (stateless, depends on all)
         └──────────┘  └──────────┘  └──────────┘
```

> **Rule:** No reverse dependency. `core` never imports from domain apps. `search` is the only consumer of many domains (it queries `roots`, `derivatives`, `words`, `quran`). Domain apps may import from `core` only.

### 1.4 Read-only invariant

- All ViewSets inherit from `ReadOnlyModelViewSet`. No `CreateModelMixin`, no `UpdateModelMixin`, no `DestroyModelMixin` — except `search` which uses `@api_view(["GET"])`.
- All Quran tables are `managed = False` (`§3`). Django never creates or migrates them.
- The only `migrate --run-syncdb` needed is for Django's own `auth` / `contenttypes` tables (empty, for admin). Never run migrations that touch `quran_words.db` Quran tables.
- Data mutations happen **offline** via `scripts/build_*.py` (e.g., `build_root_glosses.py`, `build_root_ai_summary.py`) which do `CREATE TABLE IF NOT EXISTS` + bulk inserts. Views never write.

---

## 2. App Directory Structure

All 8 apps use a single **Flat App** pattern. There is no Package App (no nested sub-apps) — the domain is small enough that flat is clearer.

### Flat App (the only pattern in this project)

```
app_name/
├── __init__.py
├── apps.py
├── models.py           # REQUIRED — managed=False models with db_table
├── serializers.py      # REQUIRED — explicit fields, never __all__
├── views.py            # REQUIRED — ReadOnlyModelViewSet or @api_view
├── urls.py             # REQUIRED — router or path() registrations
├── selectors.py        # [Optional] — only if read logic >50 lines (see §4)
├── tests.py            # REQUIRED — at least smoke coverage
└── migrations/         # usually empty (no Quran migrations)
```

**`selectors.py` is optional, not required.** Unlike Judicia where `services.py` + `selectors.py` are mandatory skeletons, this read-only project keeps views thin with inline helpers (`enrich_roots`, `attach_glosses`) until the logic justifies extraction. When you extract, follow [§4](#4-views-filtering--selectors-optional).

### Decision rule

- Domain models ≤ 3 → **Flat App** (all current apps).
- New domain with >3 unrelated models → new sibling app.
- New domain that is a 1:1 extension of an existing root (like `RootGloss`) → keep in the same app.

### 2.1 `INSTALLED_APPS` registration

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "core",
    "quran",
    "words",
    "morphology",
    "roots",
    "derivatives",
    "sources",
    "search",
]
```

No dotted sub-app paths, no `AppConfig.label` tricks — every app is top-level. The project name is `config` (not `quran` — renamed to avoid collision with the `quran` domain app, see `IMPLEMENTATION_PLAN.md:71`).

---

## 3. Model Standards

### 3.1 Inheritance

All concrete Quran models use `models.Model` directly with `managed = False` — there is no `BaseModel` with `id`/`created_at`/`is_deleted` because the data is linguistic, not auditable. Do not add `created_at` to Quran tables.

```python
class Root(models.Model):
    root = models.TextField(unique=True)

    class Meta:
        managed = False
        db_table = "roots"

    def __str__(self):
        return self.root
```

### 3.2 Field conventions

- **`db_table` is always explicit**, snake_case, matching the SQLite table name exactly (`roots`, `masadir`, `word_morphology`, `root_ai_summary`). Never rely on Django's default `app_model` naming.
- **`managed = False` on every Quran table.** This is the most important line in every `Meta`. Forgetting it risks a migration that drops the 114 MB database.
- **FKs across apps use string references** to avoid circular imports:
  ```python
  root = models.ForeignKey("roots.Root", models.DO_NOTHING, db_column="root_id")
  root_id = models.OneToOneField("roots.Root", models.DO_NOTHING, primary_key=True, db_column="root_id", related_name="gloss")
  ```
- **Choices:** where a field has a closed set (e.g., `Surah.revelation_type` = `مكية`/`مدنية`), declare as `models.TextChoices` inside the model. Never raw `CHOICES = [...]` lists, never integer magic numbers.
- **Money/amounts:** not applicable here. If added later, store as integer smallest unit.
- **`verbose_name` / `help_text`:** wrap in `gettext_lazy` (`_("...")`) if the admin will be used; not required for pure API tables but encouraged for new fields.

### 3.3 Meta

- `db_table` always set. `ordering` for time-series or natural order (e.g., `Surah` ordered by `id`).
- `indexes` for fields used in filter / search (e.g., `masadir.masdar_plain` has an index for `?root=` lookups).
- No `verbose_name_plural` needed unless admin is exposed.

### 3.4 URL management on models

Not currently used (no `get_absolute_url`). If you add detail pages that need stable URLs, add `get_absolute_url` returning `reverse("api:roots-detail", kwargs={"pk": self.pk})` — but the frontend currently builds URLs client-side via `lib/api.ts`.

---

## 4. Views, Filtering & Selectors (Optional)

This backend replaces the heavy Manager pattern with **thin ViewSets + composable helpers**. Selectors are optional extraction, not mandatory scaffolding.

| File | Responsibility | Returns |
| --- | --- | --- |
| `views.py` | Thin ViewSets / `@api_view` functions — declare `queryset`, `serializer_class`, `filterset_fields`, and `get_queryset` filtering via `normalize_query` | `Response` |
| `selectors.py` (optional) | Complex read logic extracted when `views.py` exceeds ~50 lines of query building | `QuerySet` or enriched list |

### 4.1 View rules

- **Inherit from `ReadOnlyModelViewSet`** for every CRUD-like endpoint. It pre-configures `SearchFilter` + `DjangoFilterBackend` + `OrderingFilter` via `REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"]` (`config/settings.py:80`).
- **Declare only domain-specific state** (4-6 class attributes); the base handles everything else:
  ```python
  class RootViewSet(viewsets.ReadOnlyModelViewSet):
      serializer_class = RootSerializer
      filter_backends = [SearchFilter, OrderingFilter]
      search_fields = ["root"]
      ordering_fields = ["root", "id"]

      def get_queryset(self):
          qs = Root.objects.all().order_by("root")
          q = self.request.query_params.get("search") or self.request.query_params.get("q")
          if q:
              nq = normalize_query(q)
              qs = qs.filter(Q(root__icontains=q) | Q(root__icontains=nq))
          return qs
  ```
- **No `get_serializer_class` override** — one serializer per view (see §5.2).
- **Override `list`/`retrieve` only when you need to enrich** (batched counts/glosses). See `roots/views.py:84-102` — it paginates manually to call `enrich_roots(instances)` before serializing.

### 4.2 Selector rules (when you need them)

- **Selectors return `QuerySet`s or enriched lists** so the caller controls slicing.
- **Extract when `get_queryset` exceeds ~50 lines** or when the same enrichment is used in multiple views (`enrich_roots` is used by both `RootViewSet` and `unified_search` — it is a natural selector candidate).
- **Never** `.all()` without further filtering in a public endpoint — always scope by the query params.
- **Skeleton** (use when you extract):
  ```python
  # selectors.py
  class RootSelector:
      @staticmethod
      def enrich(roots: list["Root"]) -> None:
          """Attach masadir/derivatives counts + gloss + ai_summary in 2-3 batched queries."""
          ...

      @staticmethod
      def search(q: str) -> QuerySet["Root"]:
          nq = normalize_query(q)
          return Root.objects.filter(Q(root__icontains=q) | Q(root__icontains=nq)).order_by("root")
  ```

### 4.3 Enrichment helpers (current pattern — keep until extraction)

`roots/views.py:13-63` defines `attach_glosses` and `enrich_roots` as module-level functions that do **batched** enrichment in 2-3 grouped queries total (not per-root). This is the canonical N+1 fix — see §6.3.

`quran/views.py:55-94` does the same for `AyahWordsViewSet.list` — collects `root_ids` from the current page only (`quran/views.py:61-69`), then fetches `gloss_map`/`ai_summary_map` in two `IN` queries and injects via `serializer_context`.

**Rule:** Keep these helpers in `views.py` until they are reused in a second view — then extract to `selectors.py` and import.

---

## 5. DRF API Standards

### 5.1 View layer

- **`ReadOnlyModelViewSet`** is the default for every endpoint. It is configured globally via `REST_FRAMEWORK` (`config/settings.py:77-89`) with:
  - `StandardPagination` (page_size 20, page_size param, max 1000 → target 100)
  - `SearchFilter` + `DjangoFilterBackend` + `OrderingFilter`
  - `JSONRenderer` + `BrowsableAPIRenderer` (browsable is intentional for `/api/` exploration)
- **`@api_view(["GET"])`** for `unified_search`, `stats`, and `word_detail` — flows that span multiple models or return custom shapes.
- **No function-based views beyond `@api_view`.** Always class-based ViewSets for resource endpoints.
- **No `get_queryset` override** unless filtering is non-standard (most views need it for `normalize_query` — that is the standard case here).

### 5.2 Serializers

- **One serializer per view** for both read paths. Do not split into `Read`/`Write` serializers — this is read-only.
- **`ModelSerializer` as the default**, with explicit `fields = [...]`. Never use `"__all__"`.
- **Computed fields** (counts, glosses, `surah_name`) are populated by the enrichment helpers before serialization, not by `SerializerMethodField` per-object queries. Where `SerializerMethodField` is used, it reads from the pre-attached `_gloss` / `_ai_summary` attributes, never from a new DB hit.
- **Money/amounts:** not applicable.

### 5.3 Filtering, pagination, sorting

- `django-filter` is the canonical filter backend; every list endpoint declares `filterset_fields` or `SearchFilter.search_fields`.
- Pagination is a single class in `core/pagination.py:4` (`StandardPagination`) — never redefined per view. `pagination_class = None` only for `SurahViewSet` (114 rows, no pagination).
- Sorting uses `OrderingFilter` with an explicit `ordering_fields = [...]` allowlist; default `ordering` is set on the queryset.

### 5.4 OpenAPI documentation (target)

- **Not yet implemented.** Target: every ViewSet decorated with `@extend_schema` (via `drf-spectacular`), tags grouped by app (`tags=["Roots"]`, `tags=["Quran"]`), examples for `search` and `word_detail`.
- Do not add it without asking — but when you do, follow the pattern in `quran-words` docs, not ad-hoc docstrings.

### 5.5 Response envelopes — Frozen v1 + Gradual Migration to v2

This is the most important contract in the backend. **User decision: gradual migration** — v1 is frozen, v2 is the target.

**v1 — Current (frozen, literal — `IMPLEMENTATION_PLAN.md` §A4):**

Paginated list response (DRF default via `StandardPagination`):
```json
{
  "count": 1642,
  "next": "http://localhost:8000/api/roots/?page=2",
  "previous": null,
  "results": [ { "id": 1, "root": "كتب", "gloss_ar": "...", "masadir_count": 5 } ]
}
```

Detail / custom responses:
```json
// GET /api/roots/19/ — single object directly (no wrapper)
{ "id": 19, "root": "رحم", "gloss_ar": "...", "ai_summary_ar": "..." }

// GET /api/search/?q=كتب — custom grouped shape (search/views.py:35-42)
{ "query": "كتب", "normalized": "كتب", "roots": [...], "masadir": [...], "derivatives": [...], "words": [...], "ayat": [...] }

// GET /api/words/1/detail/ — custom detail (words/views.py:156-178)
{ "word": {...}, "root": {"id":1,"root":"كتب","ai_summary_ar":...}, "occurrences": [...], "masadir": [...], "derivatives": [...], "meanings": [...] }

// GET /api/stats/ — flat object
{ "surahs": 114, "ayat": 6236, "words": 21295, "roots": 1642, "masadir": 5273, "derivatives": 16245, "word_occurrences": 77429 }
```

Error response (DRF default, not yet unified):
```json
{ "detail": "Not found." }
{ "detail": "q must be at least 2 chars" }
```

**v2 — Target (gradual migration, not yet active):**

Success envelope (every 2xx via `core/renderers.EnvelopeJSONRenderer` — to be created):
```json
{
  "data": <resource | list>,
  "meta": {
    "pagination": {
      "count": 100,
      "page_size": 20,
      "current_page": 1,
      "total_pages": 5,
      "next": "http://.../?page=2",
      "previous": null
    }
  }
}
```
- `data` is the resource for detail endpoints and the list of items for list endpoints.
- `meta` is `{}` for detail endpoints (no `pagination` key). `meta.pagination` exists only on paginated list endpoints.
- `next` / `previous` are absolute URLs or `null`.
- `204 No Content` returns an empty body (no envelope).

Error envelope (every 4xx/5xx via `core/exceptions/handler.py` — to be created):
```json
{
  "error": {
    "code": "search.query_too_short",
    "message": "q must be at least 2 characters.",
    "details": { "min_length": 2, "received": 1 }
  }
}
```
- `code` is stable, `snake_case`, dot-namespaced (`domain.action_outcome`). Frontend switches on `code`, never on message text.
- `message` is human-readable, locale-aware (from `Accept-Language` when i18n is added).
- `details` is optional structured context.

**Migration rules (gradual, per user decision):**

1. **Never break v1 without a deprecation window.** v1 and v2 must coexist behind a version flag or `Accept` header, or v2 ships under `/api/v2/` when it lands.
2. New error paths should already use the v2 `code` shape (even if rendered through the v1 envelope for now) so the frontend can start switching on `code`.
3. The `smoke_api.py` baseline must be updated atomically when v2 is enabled — the diff must be reviewed and approved.
4. No view should hand-roll error JSON — raise a typed `APIError` subclass (`NotFoundError`, `ValidationFailedError`) and let the handler render the envelope.

### 5.6 API versioning

- Single version prefix `/api/` today (no `/v1/` yet). When v2 envelope lands, it will ship under `/api/v2/` with a deprecation window for `/api/`.
- Breaking changes never ship under the same prefix without a version bump.

### 5.7 URL split

Today all routes are public `GET` under `api/` (`config/urls.py:4`):
```python
api_patterns = [
    path("", include("quran.urls")),
    path("", include("words.urls")),
    path("", include("morphology.urls")),
    path("", include("roots.urls")),
    path("", include("derivatives.urls")),
    path("", include("sources.urls")),
    path("", include("search.urls")),
]
```
Top-level layout:
```
/admin/       — Django admin (no Quran data)
/api/         — all v1 API (public, no auth)
/api/schema/  — (target) OpenAPI JSON
/api/docs/    — (target) Swagger UI
```

When auth is added (not planned), follow the `urls/v1/opened.py` vs `urls/v1/secured.py` split with `PublicPathMiddleware` — ask first.

---

## 6. Filtering, Normalization & N+1 Prevention

### 6.1 Arabic normalization

`core/utils.py:14` is the **single source of truth** for Arabic search normalization:

```python
DIACRITICS_RE = re.compile(r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]")
def strip_diacritics(s: str) -> str: ...
def normalize_ar(s: str) -> str:  # strip_diacritics + unify ا/ى forms + trim
def normalize_query(q: str) -> str: ...
```

- Every view that filters on Arabic text **must** call `normalize_query(q)` and filter on both `field__icontains=q` and `field__icontains=nq` and `field_plain__icontains=nq` where `*_plain` columns exist (`words.text_plain`, `ayat.text_uthmani_plain`).
- The frontend mirror `frontend/src/lib/normalize.ts:15` must be kept identical — parity is verified by a shared test or by comparing `normalize_ar("ٱلرَّحْمـٰنِ") == "الرحمن"` on both sides.
- Never inline the regex in a view — always call the helper.

### 6.2 Filtering conventions

```python
# Canonical — dual filter on raw + normalized
q = self.request.query_params.get("search") or self.request.query_params.get("q")
if q:
    nq = normalize_query(q)
    qs = qs.filter(Q(root__icontains=q) | Q(root__icontains=nq))
```

For `words` and `ayat`, also filter on `*_plain` columns (pre-normalized at build time via `scripts/build_plain_columns.py`):
```python
qs = qs.filter(
    Q(text__icontains=q)
    | Q(text_clean__icontains=q)
    | Q(text_clean__icontains=nq)
    | Q(text_plain__icontains=nq)
)
```

### 6.3 N+1 Prevention (mandatory)

Every list view that enriches with counts or glosses **must** batch:

```python
# Good — 2-3 grouped queries total (roots/views.py:32-53)
masadir_counts = {row["root_ref_id"]: row["cnt"] for row in Masdar.objects.filter(root_ref_id__in=ids).values("root_ref_id").annotate(cnt=Count("id"))}
gloss_map = {g.root_id_id: g for g in RootGloss.objects.filter(root_id__in=ids)}
for r in roots:
    r.masadir_count = masadir_counts.get(r.id, 0)
    r._gloss = gloss_map.get(r.id)
```

```python
# Good — Prefetch + page-scoped batch (quran/views.py:46-82)
qs.prefetch_related(Prefetch("wordayah_set", queryset=WordAyah.objects.select_related("word").prefetch_related("wordmorphology__root"), to_attr="prefetched_wordayah"))
# then collect root_ids from current page only → two IN queries for gloss_map/ai_summary_map
```

**Anti-patterns to refactor on sight:**

- Loop with per-object `RootMeaning.objects.filter(root_id=r.id).count()` — N queries.
- `instance.wordmorphology` access without `select_related`/`prefetch_related`.
- `Word.objects.filter(...).exists()` followed by the same filter again (doubles the query — cache or use `if qs.exists(): qs = qs_alt` only when the fallback is rare, as in `words/views.py:47-54`).

---

## 7. URL Routing

| Path | App | View | Notes |
| --- | --- | --- | --- |
| `GET /api/surahs/` | `quran` | `SurahViewSet` | 114 rows, `pagination_class = None` |
| `GET /api/surahs/{id}/` | `quran` | `SurahViewSet` | detail |
| `GET /api/ayat/` | `quran` | `AyahViewSet` | `?surah=1&ayah=2` |
| `GET /api/ayat/{id}/` | `quran` | `AyahViewSet` | detail |
| `GET /api/ayah-words/` | `quran` | `AyahWordsViewSet` | `?surah=1&root=كتب&page_size=50` — paginated, nested words+morphology |
| `GET /api/words/` | `words` | `WordViewSet` | `?search=رحمن&q=&root=كتب&surah=1` |
| `GET /api/words/{id}/` | `words` | `WordViewSet` | detail |
| `GET /api/words/{id}/detail/` | `words` | `word_detail` | custom: word+occurrences+masadir+derivatives+meanings |
| `GET /api/word-ayah/` | `words` | `WordAyahViewSet` | `?surah=1&pos=N&root=كتب` |
| `GET /api/lemmas/` | `morphology` | `LemmaViewSet` | list |
| `GET /api/morphology/` | `morphology` | `MorphologyViewSet` | `?pos=N&root=كتب` (raw `word_morphology`) |
| `GET /api/roots/` | `roots` | `RootViewSet` | `?search=كتب&q=&page=1` — enriched with counts+gloss |
| `GET /api/roots/{id}/` | `roots` | `RootViewSet` | detail enriched |
| `GET /api/meanings/` | `roots` | `RootMeaningViewSet` | `?root=كتب&root_id=19&q=` |
| `GET /api/masadir/` | `derivatives` | `MasdarViewSet` | `?root=كتب&q=&page_size=20` |
| `GET /api/derivatives/` | `derivatives` | `DerivativeViewSet` | `?root=علم&is_quranic=1` |
| `GET /api/sources/` | `sources` | `SourceViewSet` | list (GPL attribution) |
| `GET /api/search/?q=&type=` | `search` | `unified_search` | `type=root\|masdar\|derivative\|word\|all` (default `all`) |
| `GET /api/stats/` | `search` | `stats` | counts for hero cards |

All paths are registered under `api/` via `config/urls.py:16`. Keep the frozen contract table in `IMPLEMENTATION_PLAN.md` §A4 in sync when you add a path — and get approval first.

---

## 8. Code Validation (Before Submitting)

**ALWAYS verify before considering a task complete. Run from the repo root:**

```bash
# 1. Syntax check every modified file
python -m py_compile backend/<app>/views.py backend/<app>/models.py

# 2. Import check (catches NameError, ImportError, MRO errors)
DJANGO_SETTINGS_MODULE=config.settings python -c "import django; django.setup(); from roots.views import RootViewSet; from quran.views import AyahWordsViewSet"

# 3. Django system check
python backend/manage.py check

# 4. Contract verification — compare against baseline (the frozen contract)
backend/.venv/bin/python backend/scripts/smoke_api.py --base http://127.0.0.1:8000/api --save /tmp/opencode/after --compare /tmp/opencode/baseline
# Must be 100% identical for v1. Any diff = breaking change → requires updated baseline + approval.

# 5. (Optional) ruff / mypy if configured
ruff check backend/
```

A task is **not** done if any of these fail.

---

## 9. Critical Constraints (Do Not Violate)

1. **Never set `managed = True`** on any Quran table — it risks dropping the 114 MB database on `migrate`.
2. **Never write to `quran_words.db` from a view** — it is read-only in production (Docker `read-only` mount). Mutations only via offline `scripts/*.py`.
3. **Never add a new endpoint without updating** `IMPLEMENTATION_PLAN.md` §A4 + `README.md` API table + `examples/*.sql` smoke coverage + getting approval.
4. **Never break the v1 envelope** (`{count,results}`) without a version bump (`/api/v2/`) and a deprecation window. The `smoke_api.py` baseline is the gate.
5. **Never diverge `normalize_ar`** between `backend/core/utils.py:14` and `frontend/src/lib/normalize.ts:15` — parity is a cross-cutting invariant (see `../AGENT.md`).
6. **Never hand-roll filtering without `normalize_query`** — every Arabic `Q` filter must cover both `q` and `nq` (and `*_plain` where available).
7. **Never introduce N+1** — every list enrichment must be batched via `values().annotate(Count)` + `IN` queries (see §6.3).
8. **Never add `services.py` for writes** — this is read-only. If you believe you need a write endpoint, ask first.
9. **Never duplicate `StandardPagination`** — use `core/pagination.py:4` only. Do not redefine per view.
10. **Never use `"__all__"` in serializers** — explicit `fields = [...]` always.
11. **Never import domain models into `core`** — dependency graph is `core` ← domain (see §1.3).
12. **Money is not applicable** — if added later, store as integer smallest unit, format with a helper.

---

## Appendix A — Quick Reference Card

**Shipped surface (15 endpoints across 8 apps):**

| App | Endpoints | Key files |
| --- | --- | --- |
| `quran` | `surahs`, `ayat`, `ayah-words` | `quran/models.py`, `views.py:15-94` |
| `words` | `words`, `word-ayah`, `words/{id}/detail/` | `words/views.py:21-178` |
| `morphology` | `lemmas`, `morphology` | `morphology/models.py` |
| `roots` | `roots`, `meanings` | `roots/views.py:13-125` |
| `derivatives` | `masadir`, `derivatives` | `derivatives/models.py` |
| `sources` | `sources` | `sources/models.py` |
| `search` | `search`, `stats` | `search/views.py:20-105` |
| `core` | `utils.normalize_ar`, `pagination.StandardPagination` | `core/utils.py`, `core/pagination.py` |

**Run the backend:**

```bash
source backend/.venv/bin/activate
python backend/manage.py migrate --run-syncdb  # auth tables only
python backend/manage.py runserver 0.0.0.0:8000 --noreload
curl http://127.0.0.1:8000/api/stats/ | jq
```

**Add a new read endpoint (checklist):**

1. Answer the 7 Golden Rule questions (§0).
2. Add `models.py` (managed=False) if new table — via `scripts/` first.
3. Add `serializers.py` with explicit `fields`.
4. Add `views.py` with `ReadOnlyModelViewSet` + `get_queryset` using `normalize_query` where needed.
5. Register in `urls.py` and include in `config/urls.py:4`.
6. Update `IMPLEMENTATION_PLAN.md` §A4 + `README.md` API table.
7. Run validation (§8) + `smoke_api.py --compare`.

