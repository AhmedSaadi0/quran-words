# AGENT.md — Quran Words Platform

> **System identity:** Quran Words (قاعدة بيانات كلمات القرآن الكريم) is a professional read-only linguistic database for the Holy Quran — from Uthmani text to precise morphological analysis, roots, masadir (verbal nouns), derivatives, and classical lexicon glosses.
>
> **Goal:** `SELECT` once and get the word + its root + its masdar + all derivatives + its meaning from Lisan al-Arab.
>
> **This file is the master orchestrator.** It contains the system identity, the monorepo map, the universal engineering principles (Clean Code, Function Design, Code Quality) that apply to every component, and the cross-cutting contracts. Domain-specific guides live next to their code.

| Subsystem | File | Status |
| --- | --- | --- |
| Backend (Django + DRF, read-only) | [`backend/AGENT.md`](backend/AGENT.md) | active |
| Frontend (Next.js 16) | [`frontend/AGENT.md`](frontend/AGENT.md) | active |

**Source-of-truth documents:**

| Document | Path | Role |
| --- | --- | --- |
| Project contract (frozen API) | [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) | `§A4` — 15 endpoints, literal paths, never break |
| Website plan (approved) | [`WEBSITE_PLAN.md`](WEBSITE_PLAN.md) | Architecture, DB, hosting decisions |
| AI summary plan | [`ROOT_AI_SUMMARY_PLAN.md`](ROOT_AI_SUMMARY_PLAN.md) | `root_ai_summary` generation |
| Backend detail | [`backend/README.md`](backend/README.md) | 8 apps, serializers, examples |
| Frontend detail | [`frontend/README.md`](frontend/README.md) | Setup, pages |
| Query examples | [`examples/queries.sql`](examples/queries.sql), [`examples/masadir_queries.sql`](examples/masadir_queries.sql) | Ground-truth SQL |
| Smoke baseline | `/tmp/opencode/baseline/` (generated) | `scripts/smoke_api.py` reference |

> When docs conflict, `IMPLEMENTATION_PLAN.md` wins; when it is silent, this file and the subsystem AGENT.md are authoritative. When subsystem AGENT.md conflicts with this file, this file wins for universal rules (§18-20).

---

## Table of Contents

1. [How to use this monorepo](#how-to-use-this-monorepo)
2. [Golden Rule: Ask Before Adding](#golden-rule-ask-before-adding)
3. [§18 — Clean Code](#18-clean-code)
4. [§19 — Function Design Rules](#19-function-design-rules)
5. [§20 — Code Quality Rules](#20-code-quality-rules)
6. [Cross-Cutting Decisions](#cross-cutting-decisions)
7. [Appendix — Naming & Conventions](#appendix--naming--conventions)

---

## How to use this monorepo

```
quran-words/
├── AGENT.md                  # ← you are here (master: identity + universal rules)
├── README.md                 # landing page (stats, quick start, troubleshooting)
├── IMPLEMENTATION_PLAN.md    # frozen contract — API paths literal
├── WEBSITE_PLAN.md           # approved architecture plan
├── ROOT_AI_SUMMARY_PLAN.md   # AI summary generation plan
├── data/
│   ├── quran_words.db        # 114 MB SQLite (Git LFS) — THE database
│   ├── arabic_roots.json     # 169 MB lexicon (LFS)
│   ├── arabic_roots.parquet  # 83 MB (LFS)
│   └── quranic_corpus_morphology.json
├── backend/                  # Django + DRF service (read-only)
│   ├── AGENT.md              # ← backend-specific rules
│   ├── config/               # settings, urls, wsgi
│   ├── core/                 # shared: normalize_ar, pagination, renderers
│   ├── quran/                # surahs, ayat, ayah-words
│   ├── words/                # words, word_ayah, word_detail
│   ├── morphology/           # lemmas, word_morphology
│   ├── roots/                # roots, root_meanings, root_glosses, root_ai_summary
│   ├── derivatives/          # masadir, derivatives, word_masdar
│   ├── sources/              # sources attribution (GPL)
│   ├── search/               # unified search + stats
│   └── scripts/smoke_api.py  # contract verifier (baseline diff)
├── frontend/                 # Next.js 16 App Router
│   ├── AGENT.md              # ← frontend-specific rules
│   ├── src/
│   │   ├── app/              # (pages) /, search, roots/[root], words/[id], surahs/[id], guide/morphology, sources
│   │   ├── components/       # site-header, search-bar, stats-cards, root-card, masdar-list, ...
│   │   └── lib/              # api.ts (single source), normalize.ts (mirror), morphology.ts
│   └── vendor/               # offline tarballs (next-16.3.2.tgz etc)
├── scripts/                  # build_db.py, build_morphology.py, build_masadir_derivatives.py, ...
└── examples/                 # queries.sql, masadir_queries.sql
```

**Reading order for a new contributor:**

1. Read **this file** end-to-end (~300 lines). It is the universal contract.
2. Open the AGENT.md of the subsystem you will work on:
   - `backend/AGENT.md` for Django (~600 lines)
   - `frontend/AGENT.md` for Next.js (~450 lines)
3. Consult `IMPLEMENTATION_PLAN.md` whenever an API or DB decision is in question — its `§A4` table is the frozen contract.
4. Consult `backend/README.md` for the 8-app responsibility map.

**Cross-cutting decisions** (normalization parity, envelope shape, pagination, Git LFS, RTL, env single-source) are coordinated **at the root in this file**. Domain implementation details (a specific ViewSet, a specific component) are coordinated in the subsystem's own AGENT.md.

---

## Golden Rule: Ask Before Adding

Before writing **any** code for a new app / endpoint / table / route, you MUST have 100% clarity. If you cannot answer every question below, **STOP and ask the user** — never proceed on guesswork.

| # | Question | Possible Answers / Notes |
| --- | --- | --- |
| 1 | **Which app does this belong to?** | `core` / `quran` / `words` / `morphology` / `roots` / `derivatives` / `sources` / `search` |
| 2 | **Does it need a new DRF endpoint?** | Yes → `views.py` + `serializers.py` + `urls.py` / No → helper only |
| 3 | **Does it touch the DB schema?** | Never — all tables are `managed=False`; new tables only via `scripts/*.py` with `CREATE TABLE IF NOT EXISTS` |
| 4 | **Does it touch Arabic normalization?** | Yes → must update **both** `backend/core/utils.py:14` and `frontend/src/lib/normalize.ts:15` identically |
| 5 | **Does it change pagination or envelope?** | Requires `smoke_api.py --compare` baseline diff + user approval (gradual migration, see below) |
| 6 | **Does it need a new frontend route?** | Yes → `src/app/**/page.tsx` (async server) + optional `components/` |
| 7 | **Does it add i18n strings?** | Must add to **both** `messages/ar.json` and `messages/en.json` (see `frontend/AGENT.md` §5) |

**NEVER guess or assume. Always ask until every question is answered with certainty.**

---

## 18. Clean Code

> **Reference:** Robert C. Martin, _Clean Code_ (2008), Chapter 5 — "Formatting": _"Functions should be followed by the functions they call. The most important functions should come first."_
>
> **Scope:** Universal. Applies to every class in every language — Python (backend), TypeScript (frontend), Bash (tooling). Examples use Python for concreteness, but the rule is language-agnostic.
>
> **Note:** This section is written for AI agents generating code. When you write or edit any class, check it against §18.1. Violating one is a bug; fix it before submitting.

### 18.1 The Core Rule (Top-Down Newspaper Metaphor)

When writing or editing a class, order its members so that the reader can understand the class by reading it **top-to-bottom without scrolling back and forth**:

1. **Class constants and `Meta` first** (if any).
2. **Public methods / entry points first**, in order of importance.
3. **Each public method is immediately followed by the private helpers it calls**, in the **exact order** they appear inside the method body.
4. **Shared helpers appear only once** — at the location of their **first** use. Subsequent callers reference them by going up.
5. **Section dividers** (`# === PUBLIC API: <name> ===`) visually separate each public-method group.

### 18.2 Visual Template

```python
class MyService:

    # 1. Class constants
    REQUIRED_FIELDS: tuple[str, ...] = (...)

    # 2. PUBLIC API: <main entry point>
    @staticmethod
    def main_action(...):
        ...
        helper_a(...)
        helper_b(...)
        ...

    # --- helpers used by main_action (in call order) ---
    @staticmethod
    def _helper_a(...):
        ...
        shared_helper(...)        # used elsewhere too
        ...

    @staticmethod
    def _helper_b(...):
        ...

    # 3. PUBLIC API: <second entry point>
    @staticmethod
    def second_action(...):
        ...
        helper_c(...)             # new helper, defined below
        helper_a(...)             # already defined above for main_action
        ...

    # --- helpers used by second_action (in call order) ---
    @staticmethod
    def _helper_c(...):
        ...
```

### 18.3 Why This Matters

| Without ordering | With Clean Code ordering |
| --- | --- |
| Helpers defined before the public method → reader jumps back | Reader reads `main_action`, sees helpers right below, understands flow in one pass |
| Helper used by 3 public methods appears 3 times (or referenced from above by all 3) | Helper appears once, at its first-use site; subsequent uses are self-documenting |
| Class reads bottom-up: details first, then high-level → backwards | Class reads top-down: high-level first, then details → natural storytelling |

### 18.4 Concrete Example (from this codebase)

`roots/views.py:13-63` follows this order:

```
PUBLIC API  enrich_roots / attach_glosses
helpers     _fetch_counts (masadir_counts, deriv_counts, meanings_counts)
            _fetch_gloss_maps
─────────────────────────────────
PUBLIC API  RootViewSet.list / retrieve
helpers     get_queryset (normalize + Q filter)
```

`quran/views.py:31-94` — `AyahWordsViewSet.list` is the public entry; its helpers (`_collect_root_ids`, `_fetch_gloss_maps`) would appear immediately below it if extracted. Today the batching logic (`quran/views.py:61-82` collecting `root_ids` → `gloss_map`/`ai_summary_map`) is inline — when extracted, keep call-order.

- `enrich_roots` is first (most reused, primary entry).
- Its helpers would appear **in the order they are called** inside `enrich_roots`.
- A helper used by both `enrich_roots` and `attach_glosses` appears **only once** — at its first-use site.

### 18.5 Applies To

| Component | Example in this project |
| --- | --- |
| Service/selector helpers | `enrich_roots`, `attach_glosses` in `roots/views.py` |
| Model classes | `Root`, `RootGloss`, `Masdar` — constants → fields → `Meta` → `__str__` |
| ViewSets | `RootViewSet`, `AyahWordsViewSet` — `queryset`/`serializer_class` → `get_queryset` → `list`/`retrieve` |
| Serializer classes | `RootSerializer`, `AyahWithWordsSerializer` — `fields` → computed `SerializerMethodField` |
| Frontend components | `SiteHeader`, `RootCard` — props → state → effects → handlers → render |
| Utility modules | `core/utils.py` — `strip_diacritics` → `normalize_ar` → `normalize_query` (call order) |
| Task/script modules | `scripts/build_*.py` — module-level functions ordered by call dependency |
| Test classes | `test_<feature>_<scenario>` hierarchy |

### 18.6 When Adding a New Method to an Existing Class

1. Decide whether it is **public** (entry point) or **private** (helper).
2. **Public**: place it in the appropriate public-method slot with a section divider; put its helpers directly below.
3. **Helper used by one public method**: place it directly below that public method's group, in call order.
4. **Helper used by multiple methods**: place it at the **first** caller's site (search the class for the first public method that calls it).

### 18.7 Anti-Patterns to Refactor On Sight

- Helper defined before the public method that calls it.
- All helpers grouped at top/bottom with no relation to callers.
- Public method defined in the middle of helper definitions.
- Two copies of the same helper (DRY violation caused by poor ordering awareness).
- A public method that calls a helper defined **after** a different public method that also uses it.

### 18.8 How To Verify

After writing or editing a class, mentally read it top-to-bottom:

> _"If I'm a new developer reading this class for the first time, do I need to scroll up to find what a method does?"_

If yes → re-order until the answer is no.

---

## 19. Function Design Rules

> **Reference:** Robert C. Martin, _Clean Code_ (2008), Chapter 3 — "Functions".
> **Scope:** Universal. Every rule uses the **Rule → Smell → Action** pattern. Check every function against these six rules. Violating one is a bug.

### 19.1 Single Responsibility (SR)

**Rule:** Every function or class has exactly one reason to change. If its name contains "and"/"or" or describes more than one verb, it violates SR.

- **Smell:** `validate_and_save()`, `fetch_and_enrich_and_paginate()`, `search_roots_and_masadir()`.
- **Action:** Split into separate functions, each with a single verb. A caller composes them: `roots = search_roots(q); masadir = search_masadir(q);`.

### 19.2 One Level of Abstraction (SLAP)

**Rule:** All statements inside a function must operate at the same level of abstraction. High-level orchestration must not be mixed with low-level details.

- **Smell:** `unified_search` calls both `Root.objects.filter(...)` (high) and `DIACRITICS_RE.sub("", s)` (low) in the same body.
- **Action:** Extract every low-level detail into a named helper (`normalize_query(q)`). The parent reads as a story of high-level steps — every line at the same altitude. In this project `core/utils.py:14` already does this; views must call `normalize_query`, never inline the regex.

### 19.3 Boolean Flag Arguments are a Smell

**Rule:** A `flag: bool` parameter almost always means the function does two different things. The name lies.

- **Smell:** `def search(q, include_ayat=True, is_quranic=None)`. Multiple booleans + sentinel values the caller must decode. Branches inside keyed on flags.
- **Action:** Split into separate functions (`search_words` vs `search_ayat`, `derivatives_quranic()` vs `derivatives_all()`), or replace with an `Enum`/strategy.

### 19.4 No Side Effects

**Rule:** A function does exactly what its name says, and nothing else. Hidden actions are bugs.

- **Smell:** `get_roots()` silently writes to cache or mutates a global. `normalize_ar()` that also logs to DB.
- **Action:** Make every side effect explicit in the name (`fetch_and_cache_roots`), or — preferred — extract the side effect and have the caller invoke it explicitly. A getter must only get.

### 19.5 Command-Query Separation (CQS)

**Rule:** A function is either a **command** (changes state, returns nothing meaningful) or a **query** (returns a value, changes nothing) — never both.

- **Smell:** `build_db()` that mutates the DB and returns a bool for "did it succeed?". `pop()`-style helpers in scripts.
- **Action:** Split into a pure command (`build()` returns `None`) and a separate query (`was_built()`, `row_exists()`). For this read-only backend, most functions are queries — keep them pure.

### 19.6 Guard Clauses & Fail Fast

**Rule:** Handle exceptional and error cases at the very top with early returns/raises. Keep the happy path at the bottom, unindented, reading linearly.

- **Smell:** Nested `if`/`else` 3+ levels deep. The success case buried inside an `else` at the bottom.
- **Action:** Each guard checks one precondition and returns/raises early. Remaining body is the linear happy path with no further nesting. Aim for zero `else` after guards.

```python
# Good — guards first, happy path last
def unified_search(request):
    q = request.query_params.get("q", "").strip()
    if not q or len(q) < 2:
        return Response({"detail": "q must be at least 2 chars"}, status=400)
    # ... happy path linearly
```

---

## 20. Code Quality Rules

> **Reference:** Robert C. Martin, _Clean Code_ — Chapters 4, 6, 7, 8. Also: Fowler, _Refactoring_; Hunt & Thomas, _The Pragmatic Programmer_.
> **Scope:** Universal. Same **Rule → Smell → Action** pattern. Apply to all code.

### 20.1 Comments Explain WHY, Not WHAT

**Rule:** Good comments explain the decision, constraint, warning, or gotcha. They never narrate what the code says.

- **Smell:** `# loop over roots` above `for r in roots:`.
- **Action:** Delete any comment that restates the code. Replace with rationale: business rule, non-obvious constraint, historical reason, or warning. If removing the comment makes the code unclear, fix the code (better names, extracted functions) instead.

```python
# Bad:  # enrich roots with counts
# Good: # Batched counts: two grouped queries total (N+1 fix — was per-root before)
```

### 20.2 Defensive Programming at Boundaries

**Rule:** Validate inputs and handle failures explicitly at every boundary: user query params, file I/O, network, DB, env vars.

- **Smell:** `int(request.query_params["page"])` without try/except. `response.json()` without checking `status_code`. `obj.field` on a value that could be `None`.
- **Action:** At every boundary, validate shape and type, wrap risky ops in try/except, log with context, and return a clear typed error. Never let a boundary failure propagate as an unhandled 500. In this project: `search/views.py:27` guard on `q` length is the canonical example.

### 20.3 Don't Return Null

**Rule:** Returning `None` forces every caller to write defensive null-checks. Absence should be an empty collection, a Null Object, or a raised exception — not a magic value.

- **Smell:** `def get_roots(): ... return None if empty`. Every caller writes `if roots is not None:`.
- **Action:** For collections, return empty `list`/`dict`. For a missing single record, raise `DoesNotExist` (DRF maps to 404) and let the handler decide. In this codebase, `search/views.py` returns `{"roots": []}` (empty list, never null) — keep it.

### 20.4 Replace Magic Numbers with Named Constants

**Rule:** Any literal number or string that carries business meaning must have a name.

- **Smell:** `if status == 4 and days > 30:` — unexplained. Same value duplicated across files.
- **Action:** Declare each literal once at module or class level with a self-documenting name. In this project:

```python
# backend/core/pagination.py:5-6
PAGE_SIZE = 20
MAX_PAGE_SIZE = 100  # target (currently 1000 — see backend/AGENT.md §8)

# frontend/src/lib/api.ts
DEFAULT_REVALIDATE_SEARCH = 300
DEFAULT_REVALIDATE_STATS = 600
```

### 20.5 Encapsulate Conditionals

**Rule:** Complex boolean expressions must be extracted into named functions or predicates. The call site should read as a natural sentence.

- **Smell:** `if user.age > 65 and user.years_active > 10 and not user.is_suspended:` — logic puzzle on every read.
- **Action:** Extract into a method with a self-documenting name: `if root.is_weak():`. Push the predicate down to the class that owns the data. In this project, `is_weak_root` checks in `scripts/build_masadir_derivatives.py` are the canonical example — extract, don't inline.

### 20.6 Law of Demeter (Only Talk to Immediate Friends)

**Rule:** A method may only invoke methods of: itself, its parameters, any object it creates, or its direct instance variables. No train-wreck chains.

- **Smell:** `wa.wordmorphology.root.root` — three levels of dotting. `ayah.surah.name_ar` in a template hand-rolled.
- **Action:** Add a delegating method on the immediate friend: `word.get_root_text()` or expose via serializer `root_text` field (already done in `MorphologySerializer`). If you need something deep, ask the top object — don't reach in. The serializers in `roots/serializers.py` and `quran/serializers.py` already encapsulate this.

---

## Cross-Cutting Decisions

These are coordinated **at the root**. Subsystem AGENT.md files must not contradict them.

### Arabic Normalization Contract (Critical)

`backend/core/utils.py:14` and `frontend/src/lib/normalize.ts:15` **must be byte-identical in behavior**:

```python
# backend/core/utils.py
DIACRITICS_RE = re.compile(r"[\u0617-\u061a\u064b-\u0652\u0656-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed\u0640]")
def normalize_ar(s: str) -> str:
    s = DIACRITICS_RE.sub("", s)
    s = s.replace("ٱ","ا").replace("ـ","").replace("آ","ا").replace("أ","ا").replace("إ","ا").replace("ى","ي")
    return s.strip()
```

```ts
// frontend/src/lib/normalize.ts — same ranges, same replacements
const DIACRITICS_RE = /[\u0617-\u061A\u064B-\u0652\u0656-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED\u0640]/g;
export function normalizeAr(s: string): string { /* identical */ }
```

- Any change to one **must** be mirrored to the other in the same commit.
- Tests must assert parity: `normalize_ar("ٱلرَّحْمـٰنِ") == "الرحمن"` on both sides.

### Database Contract

- All Quran tables are `managed = False` with explicit `db_table` (e.g., `roots`, `masadir`). **Never** set `managed = True`.
- FKs across apps use string references: `FK("roots.Root")`, never direct imports that create circular dependencies.
- DB file is `BASE_DIR.parent / "data" / "quran_words.db"` with `timeout: 20` and `CONN_MAX_AGE = 60` (`backend/config/settings.py:64-70`).
- New tables only via `scripts/*.py` with `CREATE TABLE IF NOT EXISTS` (like `root_glosses`, `root_ai_summary`). Zero Django migrations for Quran data.
- Never write to `quran_words.db` from Django views — it is read-only in production (Docker `read-only` mount).

### Pagination Contract

- Default `page_size = 20` (`backend/core/pagination.py:5`), `page_size` query param, **target** `max_page_size = 100` (currently `1000` — tighten gradually, see `backend/AGENT.md`).
- Frontend drives pagination from `Paginated<T>.next` / `previous` URLs.

### Git LFS Contract

- `data/** filter=lfs` in `.gitattributes`. Never commit `*.db` / `*.parquet` without LFS.
- After `git clone --depth 1`, run `git lfs pull` to fetch `quran_words.db` (114 MB).

### i18n & RTL Contract

- Arabic is the default content language; English is secondary (bilingual immediate, see `frontend/AGENT.md` §5).
- Every page renders `<html dir="rtl">` for `ar` and `dir="ltr"` for `en`; use logical CSS (`text-start`/`text-end`, `ps`/`pe`, `ms`/`me`), never `text-left`/`text-right`.
- Frontend i18n keys live in `messages/ar.json` + `messages/en.json` with parity enforcement.

### Environment Single Source

- `API_URL` is defined **once** in `frontend/src/lib/api.ts:6` from `NEXT_PUBLIC_API_URL`. Never duplicate `process.env.NEXT_PUBLIC_API_URL` elsewhere.
- Backend `SECRET_KEY` / `ALLOWED_HOSTS` / `CORS` are dev-open (`*`) but must be restricted in production via env.

### API Contract Stability

- `IMPLEMENTATION_PLAN.md` §A4 is the frozen contract: 15 endpoints with literal paths. Any breaking change requires:
  1. Update `IMPLEMENTATION_PLAN.md` §A4 table,
  2. Run `backend/scripts/smoke_api.py --compare` against the baseline in `/tmp/opencode/baseline/`,
  3. Explicit user approval.
- Gradual envelope migration (v1 `{count,results}` → v2 `{data,meta}`) is documented in `backend/AGENT.md` §5 — never break v1 without a deprecation window.

---

## Appendix — Naming & Conventions

| Context | Convention | Example |
| --- | --- | --- |
| Python/Django | `snake_case` for fields, methods, table names | `text_uthmani_plain`, `root_glosses`, `enrich_roots` |
| TypeScript (cross-boundary) | `snake_case` for API fields (mirror serializers) | `masdar_plain`, `is_attested`, `page_size` |
| TypeScript (local) | `camelCase` for local helpers, components | `normalizeAr`, `SiteHeader`, `RootCard` |
| DB tables | `snake_case`, plural where natural | `roots`, `masadir`, `word_morphology`, `root_ai_summary` |
| API query params | `snake_case` | `?search=كتب&page_size=20&is_quranic=1` |
| Frontend files | `kebab-case` | `site-header.tsx`, `search-bar.tsx`, `normalize.ts` |
| i18n keys | `camelCase`, namespaced | `common.search`, `roots.meanings`, `errors.notFound` |

> If a convention here conflicts with a subsystem AGENT.md, this file wins for cross-cutting concerns; otherwise the subsystem guide is authoritative for its domain.

