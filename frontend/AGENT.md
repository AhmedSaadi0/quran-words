# AGENT.md — Quran Words Frontend (Next.js 16)

> **Subsystem:** Next.js 16 App Router web client for the Quran Words linguistic database (roots, masadir, derivatives, morphological analysis, Uthmani text).
>
> **This file is the frontend-specific guide.** It defines the stack, directory map, Server/Client boundary, bilingual i18n contract, data layer (single path via `lib/api.ts`), component & styling standards, and the mandatory backend envelope contract. The **universal** engineering principles (Clean Code §18, Function Design §19, Code Quality §20) live in the root [`AGENT.md`](../AGENT.md) and apply unchanged to every TypeScript/TSX file.
>
> **Source-of-truth documents:**

| Document | Path |
| --- | --- |
| Frozen API contract | [`../IMPLEMENTATION_PLAN.md`](../IMPLEMENTATION_PLAN.md) §A4 |
| Backend subsystem guide | [`../backend/AGENT.md`](../backend/AGENT.md) |
| Project overview | [`../README.md`](../README.md) |
| AI summary plan | [`../ROOT_AI_SUMMARY_PLAN.md`](../ROOT_AI_SUMMARY_PLAN.md) |

> When this file conflicts with the backend guide, the frozen contract wins; when those are silent, this file is authoritative. Universal rules (§18-20) always win.

---

## Table of Contents

0. [Golden Rule: Never Assume — Always Ask](#0-golden-rule-never-assume--always-ask)
1. [Stack & Global Conventions](#1-stack--global-conventions)
2. [Directory Map](#2-directory-map)
3. [Server/Client Boundary](#3-serverclient-boundary)
4. [State Management (URL-Driven)](#4-state-management-url-driven)
5. [i18n — Bilingual Immediate (Arabic + English)](#5-i18n--bilingual-immediate-arabic--english)
6. [Data Layer & Backend Contract](#6-data-layer--backend-contract)
7. [BFF Route Handlers (Target, Not Yet Active)](#7-bff-route-handlers-target-not-yet-active)
8. [Components & Styling](#8-components--styling)
9. [Forms](#9-forms)
10. [Hooks](#10-hooks)
11. [Code Validation (Before Submitting)](#11-code-validation-before-submitting)
12. [Critical Constraints (Do Not Violate)](#12-critical-constraints-do-not-violate)
13. [Known Inconsistencies & Transitional TODOs](#13-known-inconsistencies--transitional-todos)
14. [Reference — Canonical Files](#14-reference--canonical-files)

---

## 0. Golden Rule: Never Assume — Always Ask

Before writing **any** code for a feature, you MUST have 100% clarity. **STOP and ask the user** — never proceed on guesswork.

| # | Question | Possible Answers |
| --- | --- | --- |
| 1 | Is this a **server component** (page, static data) or **client component** (interactive)? | Server pages fetch via `api.*` (`lib/api.ts`) / Client components use hooks, events, `useState` |
| 2 | Does it need **new data** from Django? | Server → new `api.*` helper in `lib/api.ts` / Client → new BFF route handler (target, see §7) |
| 3 | Does it **mutate** data? | No — current app is read-only; mutations only via offline `scripts/` on the backend. If you think you need a mutation, ask first. |
| 4 | Does it need a **new route** (`app/**/page.tsx`)? | Yes → `app/<feature>/page.tsx` (async server) + optional `components/<feature>/` |
| 5 | Does it show **user-facing text**? | Add keys to **both** `messages/ar.json` and `messages/en.json` (see §5) |
| 6 | Is it a **list with filters/pagination**? | URL search params driven, server-rendered + `<Suspense>` + `PaginationControls` |

### Resulting action

Once every question is answered, apply the pattern from the matching section below. **NEVER guess or assume the structure.**

---

## 1. Stack & Global Conventions

| Item | Value |
| --- | --- |
| Framework | Next.js **16** App Router (Turbopack for dev), React **19** — App Router only, no `pages/` dir |
| Language | TypeScript, `strict: true` (`tsconfig.json` → `@/*` alias) |
| Styling | Tailwind CSS **v4** (CSS-first in `app/globals.css`, NO `tailwind.config.*`) |
| UI primitives | shadcn-style on **Radix UI** (`@radix-ui/react-*`) — `components/ui/` (`button`, `input`, `card`, `tabs`, `badge`, `skeleton`, `popover`, `tooltip`, `separator`) |
| Icons | `lucide-react` only |
| i18n | `next-intl` — locales `ar` (default) + `en`, RTL for Arabic (see §5) — **bilingual immediate** per user decision |
| Fonts | `next/font` — **Amiri** for Quran text (`app/layout.tsx:18` preconnect) |
| State | **URL search params** are the state for filters/pagination/search; local `useState` for UI toggles — **no global store** (no Zustand, no Redux) |
| Data client | `lib/api.ts` — single source for `API_URL` + typed helpers + `Paginated<T>` |
| Normalization | `lib/normalize.ts` — JS mirror of `backend/core/utils.py:14` (must stay identical) |
| Path alias | `@/*` → `src/*` |

### Code style rules

- **Semicolons + single quotes dominant** in this codebase (`lib/api.ts:6` uses `;`, `components/site-header.tsx:1` uses `"use client";` with `;`). New code follows the existing convention: **semicolons, single quotes for TS, double quotes for JSX attributes**.
- **camelCase** for JS/TS identifiers (`normalizeAr`, `RootCard`). **snake_case** for everything that crosses the Django boundary: query params, request bodies, response fields (`page_size`, `masdar_plain`, `is_quranic`) — see §6.
- **Components:** named exports only — `export function X()` / `export const x = ...`. **NEVER** `React.FC`, **NEVER** `export default` for components. **Pages** (`app/**/page.tsx`) use `export default async function XPage()` — Next.js requires default for pages only.
- **Props:** `interface [ComponentName]Props` — never bare `interface Props` (see `components/search-bar.tsx:10` `SearchBarProps`).
- **Type imports inline** — `import type { Metadata } from "next"`; `import type { RootItem } from "@/lib/api"`.
- **No new libraries** without asking: no new state library, no new UI kit, no new HTTP client, no new form library (unless §9 target).

---

## 2. Directory Map

```
frontend/                               ← APP ROOT (relative paths in this file start here)
├── src/
│   ├── app/
│   │   ├── layout.tsx                  # Root layout: <html lang/dir>, Amiri font, SiteHeader, footer
│   │   ├── globals.css                 # Tailwind v4 entry + @theme tokens + CSS variables
│   │   ├── page.tsx                    # Home: SearchBar + StatsCards + Root grid + Pagination (async server)
│   │   ├── search/page.tsx             # Grouped search results (roots→masadir→words→ayat)
│   │   ├── roots/[root]/page.tsx       # Root detail: meanings/masadir/derivatives/words tabs
│   │   ├── words/[id]/page.tsx         # Word detail: morph table + occurrences + masadir grid
│   │   ├── surahs/[id]/page.tsx        # Mushaf view: ayah-words with hover Popover
│   │   ├── guide/morphology/           # Morphology glossary (lib/morphology.ts → 59 terms, SSG)
│   │   │   ├── page.tsx                # index
│   │   │   └── [term]/page.tsx         # 58 SSG term pages
│   │   ├── sources/page.tsx            # GPL attribution (sources API)
│   │   └── api/                        # (target) BFF route handlers proxying to Django (see §7)
│   ├── components/
│   │   ├── site-header.tsx             # "use client" header with responsive SearchBar toggle
│   │   ├── search-bar.tsx              # "use client" debounced (300ms) → router.push /search?q=
│   │   ├── root-card.tsx               # Root grid card + gloss/ai_summary display
│   │   ├── pagination-controls.tsx     # Page nav driven by ?page=
│   │   ├── ayah-view.tsx               # Mushaf ayah rendering + word hover Popover
│   │   ├── masdar-list.tsx             # Masadir list with is_attested gold badge
│   │   ├── derivative-grid.tsx         # Derivatives grid with is_quranic filter
│   │   ├── morph-tooltip.tsx           # Morphology popover content (lib/morphology.ts terms)
│   │   └── ui/                         # button, input, card, tabs, badge, skeleton, popover, ...
│   └── lib/
│       ├── api.ts                      # THE data layer — API_URL + Paginated<T> + api.* helpers
│       ├── normalize.ts                # stripDiacritics + normalizeAr (mirror backend)
│       ├── morphology.ts               # Single source for 59 morph terms (TERMS, getTerm, TABLE_FIELDS)
│       └── utils.ts                    # cn() (clsx + tailwind-merge) only
├── messages/                           # (target bilingual) ar.json + en.json — see §5
├── public/                             # static assets
├── vendor/                             # offline tarballs (next-16.3.2.tgz, swc, sharp)
├── next.config.ts                      # unoptimized images, allowedDevOrigins
└── tsconfig.json                       # strict: true, @/* alias
```

**Where new code goes:**

| What | Where |
| --- | --- |
| New page | `src/app/<feature>/page.tsx` (async server) |
| New screen logic | `src/components/<feature>/*.tsx` (kebab-case files) |
| New shared UI | `src/components/ui/` (only if reusable across 2+ features) |
| New i18n keys | `messages/ar.json` + `messages/en.json` (both, same key) |
| New API type/helper | `src/lib/api.ts` (single file, never duplicate) |
| New hook | `src/hooks/use-<feature>.ts` (if needed) |

---

## 3. Server/Client Boundary

### Pages are ALWAYS async server components (Next 16)

Every page under `src/app/**` is an **async server component** (no `"use client"` unless it truly needs interactivity):

```tsx
// src/app/page.tsx:16 — canonical example
interface HomePageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);

  const [stats, roots] = await Promise.all([
    api.stats(),
    api.roots({ page }),
  ]);

  return (
    <div className="space-y-10">
      <SearchBar compact={false} />
      <StatsCards stats={stats} />
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {roots.results.map((r) => <RootCard key={r.id} root={r} />)}
      </div>
      <PaginationControls page={page} count={roots.count} pageSize={20} basePath="/" />
    </div>
  );
}
```

### Mandatory page rules

1. **Next 16 async `params` / `searchParams`** — always `Promise<...>` and always `await`ed. Never sync destructuring.
2. **Data fetching via `api.*` helpers** (`lib/api.ts:224` `api.stats()`, `api.roots()`, `api.search()`, etc.) — never hand-roll `fetch("http://...")`.
3. **Parallel fetching** with `Promise.all` where possible (see `page.tsx:20`).
4. **Revalidation:** `get<T>(path, params, revalidate)` uses `next: { revalidate }` (stats 600, search 300, wordDetail 3600) — tune per endpoint volatility, never `no-store` without reason.
5. **Loading:** wrap async inner components in `<Suspense fallback={<Skeleton />}>` where needed.
6. **Pass serialized plain data as props** to client children — never serialize JSON strings, never re-fetch the same data in a client component.

### `"use client"` rules

- A component is client only if it uses hooks (`useState`, `useEffect`), event handlers, `useRouter`, or browser APIs.
- Server components are **pure presentational + data fetching** — no hooks, no events; they may embed client children.
- `"use client"` at the very top of the file (see `components/site-header.tsx:1`, `components/search-bar.tsx:1`).
- Current client components: `SiteHeader`, `SearchBar`, `AyahView` (popover), `RootCard` (interactive parts) — keep the list minimal.

---

## 4. State Management (URL-Driven)

**There is no global store.** Do not create one (no Zustand, no Redux, no Context for domain data).

| State type | Where it lives | Example |
| --- | --- | --- |
| Filters, search query, pagination | **URL search params** (`?q=كتب&page=2&root=علم`) — server reads `searchParams` | `page.tsx:17` `searchParams: Promise<{page}>` |
| UI toggles (mobile search open, popover) | **Local `useState`** inside the component | `site-header.tsx:11` `isSearchOpen`, `search-bar.tsx:24` `value` |
| Domain data (roots, words, ayat) | **Server-fetched via `api.*`** and passed as props | `page.tsx:20` `api.roots({page})` |

### Rules

1. **Never** add a new global store or React Context for domain data — extend URL params or local state.
2. **Derived data = pure helper functions** (not hooks). Example: `lib/morphology.ts:260` `getTerm(field, value)` — testable, no hooks.
3. **Select only what you need** — server pages fetch exactly the needed slice (`api.roots({page})`, not all 1,642).
4. UI-only state (selected tab, hover) stays in **local `useState`** inside the view — never in URL unless it should be shareable/bookmarkable.

---

## 5. i18n — Bilingual Immediate (Arabic + English)

> **User decision: bilingual immediate.** Both `ar` (default) and `en` must be supported from now on via `next-intl`. Arabic content remains primary; English is secondary.

### Stack

- `next-intl` — locales `ar` (default, RTL) + `en` (LTR).
- Message files: `messages/ar.json` + `messages/en.json` (single JSON per locale, namespaced keys) — **both must stay in parity**.
- Routing: `i18n/routing.ts` (or `src/i18n/routing.ts`) with `defineRouting` + `createNavigation` helpers.

### Rules

1. **Every user-facing string** comes from the message files. **Never** hardcode Arabic/English in components — including labels like "Close", "Save", "Search".
2. **Add keys to BOTH** `messages/ar.json` and `messages/en.json` — same namespace, same key, same interpolation placeholders (`{count}`, `{query}`).
3. **Namespaces per domain** — one top-level key per feature: `common`, `nav`, `home`, `search`, `roots`, `words`, `surahs`, `guide`, `sources`, `errors`. Reuse `common` for shared strings; create a new namespace only for a new domain.
4. Keys are **camelCase**, nested where natural (`home.title`, `search.placeholder`, `roots.tabs.meanings`).
5. **Client:** `const t = useTranslations("namespace")` then `t("key")`. **Server:** `const t = await getTranslations("namespace")`.
6. **`setRequestLocale(locale)` in every page** after `await params` when using `next-intl` App Router setup.
7. **ALL links MUST carry the locale prefix** when using `next-intl` routing (`href="/"` via `Link` from `i18n/navigation` handles it; never bare `href="/search"` without the helper if locale prefix is enabled).
8. **Interpolation:** `t("count", { count: n })` with `{count}` placeholders in the message text.
9. **Current transitional state:** i18n is not yet wired in the codebase (hardcoded Arabic in `page.tsx:28`, `search-bar.tsx:97`). New code must still use `next-intl` keys; migrate existing hardcoded strings opportunistically — do not copy the hardcoded pattern into new code.

### Example (target)

```json
// messages/ar.json
{
  "common": { "search": "بحث", "roots": "الجذور", "loading": "جاري التحميل..." },
  "home": { "title": "كلمات القرآن", "subtitle": "تصفح الكلمات القرآنية الفريدة مع جذورها المدققة" },
  "search": { "placeholder": "ابحث بجذر: كتب / بمصدر: كتابة / بكلمة: عَلِيم", "resultsFor": "نتائج البحث عن \"{query}\"" }
}
// messages/en.json — same keys, English values
{
  "common": { "search": "Search", "roots": "Roots", "loading": "Loading..." },
  "home": { "title": "Quran Words", "subtitle": "Browse Quranic words with verified roots" },
  "search": { "placeholder": "Search by root: كتب / masdar: كتابة / word: عَلِيم", "resultsFor": "Results for \"{query}\"" }
}
```

### RTL

- `app/layout.tsx:17` currently hardcodes `<html lang="ar" dir="rtl">`. With `next-intl`, this becomes dynamic: `lang={locale}` and `dir={locale === "ar" ? "rtl" : "ltr"}`.
- Use logical CSS (`text-start`/`text-end`, `ps`/`pe`, `ms`/`me`, `start-3`/`end-3`), never `text-left`/`text-right` or `left`/`right` for directional UI.
- Directional icons branch on locale where needed (e.g., chevrons with `rtl:rotate-180`).

---

## 6. Data Layer & Backend Contract

### 6.1 The single data path (current — no BFF)

```
Server page  →  api.* (lib/api.ts)  →  Django /api/*
```

There is **exactly one** data path today. Client components never call Django directly — they navigate via `router.push("/search?q=...")` and let the server page fetch.

| Helper | Signature | Purpose |
| --- | --- | --- |
| `api.stats()` | `() => Promise<Stats>` | Hero counts (revalidate 600) |
| `api.roots(params)` | `({q?, page?}) => Promise<Paginated<RootItem>>` | Roots grid (revalidate 3600) |
| `api.search(q, type)` | `(string, string) => Promise<SearchResult>` | Unified search (revalidate 300) |
| `api.masadir(params)` | `({root?, q?, page?, page_size?}) => Promise<Paginated<Masdar>>` | Masadir list |
| `api.derivatives(params)` | `({root?, q?, is_quranic?, page?}) => Promise<Paginated<Derivative>>` | Derivatives grid |
| `api.meanings(params)` | `({root?, root_id?, q?}) => Promise<Paginated<Meaning>>` | Lexicon meanings |
| `api.words(params)` | `({q?, root?, masdar?, surah?, page?}) => Promise<Paginated<Word>>` | Words with filters |
| `api.wordDetail(id)` | `(number) => Promise<WordDetail>` | Word + occurrences + masadir + derivatives (revalidate 3600) |
| `api.ayahWords(params)` | `({surah?, root?, page?, page_size?}) => Promise<Paginated<AyahWithWords>>` | Mushaf view (revalidate 3600) |
| `api.sources()` | `() => Promise<Source[]>` | GPL attribution (revalidate 86400) |

All return the parsed Django envelope — see §6.2. `lib/api.ts:196` `buildUrl` and `lib/api.ts:206` `get<T>` are the only places that construct URLs or call `fetch`.

### 6.2 Backend response envelope (MANDATORY contract — v1 frozen, v2 gradual)

> **User decision: gradual migration.** v1 is frozen; v2 (`{data,meta}`/`{error:{code}}`) is the target. See `backend/AGENT.md` §5.5 for full spec. Frontend must handle **both** during the transition.

**v1 — Current (frozen — `IMPLEMENTATION_PLAN.md` §A4):**

Paginated (list endpoints via `StandardPagination`):
```json
{ "count": 1642, "next": "http://.../api/roots/?page=2", "previous": null, "results": [...] }
```

Detail / custom:
```json
// GET /api/roots/19/ → single object directly
{ "id": 19, "root": "رحم", "gloss_ar": "الرحمة...", "ai_summary_ar": "..." }

// GET /api/search/?q=كتب → grouped
{ "query": "كتب", "normalized": "كتب", "roots": [...], "masadir": [...], "derivatives": [...], "words": [...], "ayat": [...] }

// GET /api/words/1/detail/ → nested
{ "word": {...}, "root": {"id":1,"root":"كتب"}, "occurrences": [...], "masadir": [...], "derivatives": [...], "meanings": [...] }
```

Error (DRF default):
```json
{ "detail": "Not found." }
```

**v2 — Target (gradual, not yet active):**

Success (every 2xx via `core/renderers.EnvelopeJSONRenderer`):
```json
{ "data": <resource | list>, "meta": { "pagination": { "count": 100, "page_size": 20, "current_page": 1, "total_pages": 5, "next": "...", "previous": null } } }
```

Error (every 4xx/5xx via `core/exceptions/handler.py`):
```json
{ "error": { "code": "search.query_too_short", "message": "q must be at least 2 characters.", "details": { "min_length": 2 } } }
```

**Hybrid i18n (mandatory when v2 lands):**

1. On an error, first try the frontend's own translation: `code → message` lookup in `messages/{ar,en}.json` (e.g., `errors.searchQueryTooShort`).
2. If no translation, fall back to the server's `message`.
3. Never display the raw `code` as UI text; never assume `{detail: ...}`.

**Typed API model (current v1 + forward-compatible):**

```ts
// lib/api.ts — current
interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[]; }
// lib/api.ts — target v2 (add when backend ships v2)
interface ApiSuccess<T> { data: T; meta: { pagination?: PaginationMeta } }
interface PaginationMeta { count: number; page_size: number; current_page: number; total_pages: number; next: string | null; previous: string | null; }
interface ApiErrorPayload { code: string; message: string; details: unknown }
```

**Wire conventions:**

- All query params, request bodies, and response fields are **snake_case** — they mirror the DRF serializers exactly (`page_size`, `is_quranic`, `masdar_plain`, `is_attested`, `text_uthmani_plain`). TypeScript interfaces preserve snake_case for API fields; local helpers use camelCase.
- List endpoints are paginated (max `page_size` 100 target); drive pagination from `count`/`next`/`previous` (v1) or `meta.pagination` (v2) and pass `page`, `page_size`, `ordering` as query params.

### 6.3 Forbidden in the data layer

- `fetch("http://...:8000/...")` from any component — always `api.*` from `lib/api.ts`.
- Writing auth/refresh/cookie logic anywhere — this is a read-only public API (no auth).
- Duplicating `API_URL` — `lib/api.ts:6` only. Any `const API_URL = process.env...` outside that file is a violation.
- Assuming DRF default error shapes after v2 — handle both `{detail}` (v1) and `{error:{code}}` (v2) during transition.
- Adding a second data path (axios, SWR, React Query, GraphQL) without asking — the single path above is the only one.

---

## 7. BFF Route Handlers (Target, Not Yet Active)

> **Not yet needed** — this is a read-only public API with no auth, so no BFF proxy is required today. The section is documented as the **target pattern** if auth or mutations are added later. Do not create BFF routes until asked.

When a BFF is needed, route handlers under `src/app/api/**/route.ts` are **thin delegates** — parse input, delegate to `proxyWithAuth()`, return. **No business logic in routes.**

```ts
// Target pattern — thin delegate (not active yet)
import { NextRequest } from "next/server";
import { proxyWithAuth } from "@/lib/api-proxy";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `/roots/${searchParams ? `?${searchParams}` : ""}`;
  return proxyWithAuth(url, "GET");
}
```

Rules (when activated):

1. URL paths are **Django-relative** (start with `/`); `proxyWithAuth` prepends `API_URL`.
2. `params` is always `Promise<{ ... }>` and always awaited: `const { pk } = await params`.
3. **Never touch `cookies()` inside a route** — auth helpers handle it (except the auth-family routes).
4. **Never write fetch/refresh logic in a route** — `proxyWithAuth` does it.
5. Response shape passes the Django envelope through **untouched** with the upstream HTTP status.

---

## 8. Components & Styling

### Naming

- **Files:** kebab-case — `site-header.tsx`, `search-bar.tsx`, `root-card.tsx`, `pagination-controls.tsx` (see existing `src/components/`).
- **Components:** `export function PascalCase(...)` — no default exports (except pages), no `React.FC`, no `const X = () =>`.
- **Props:** `interface [ComponentName]Props` in the same file, above the component (see `search-bar.tsx:10` `SearchBarProps`).

```tsx
interface RootCardProps {
  root: RootItem;
  className?: string;
}

export function RootCard({ root, className }: RootCardProps) {
  ...
}
```

### Styling rules

1. **`cn()` for every conditional class** — `import { cn } from "@/lib/utils"` (clsx + tailwind-merge).
2. **Design tokens ONLY** for surfaces — `bg-background`, `text-muted-foreground`, `border-border`, `bg-destructive/10 text-destructive rounded-lg p-4`. **NEVER raw hex colors** for surfaces.
3. **UI primitives come from `components/ui/`** (shadcn on Radix): `Button`, `Card`, `Input`, `Tabs`, `Badge`, `Skeleton`, `Popover`, `Tooltip`, `Separator`. Variants via `cva` only inside `components/ui/`.
4. **Modals/Popovers:** use `components/ui/popover` — **never hand-roll `fixed inset-0 z-50 bg-black/60` overlays** (use the existing `morph-tooltip.tsx` pattern for word hover).
5. **Icons:** `lucide-react`, individual imports, standard sizes `size-4` / `size-5`.
6. **RTL:** use logical properties (`pe-9`, `ps-9`, `ms-auto`, `start-3`, `end-3`) and `rtl:rotate-180` on directional chevrons. Never `left/right` for directional UI.
7. **Dark mode:** `dark:` variants via class strategy (`.dark` on `<html>`). Not yet wired — add only if requested.
8. **Images:** `next/image` with `unoptimized: true` (`next.config.ts:7`) — no remote images in this app. Use placeholder fallback if needed.
9. **Feedback:** inline banners for errors (`bg-destructive/10 text-destructive rounded-lg p-4 mb-4`) — no toast library yet (ask before adding `sonner` etc.).

### Reusable shared components — check before building

`StatsCards`, `RootCard`, `PaginationControls`, `AyahView`, `MasdarList`, `DerivativeGrid`, `MorphTooltip`, `SearchBar`, skeletons — before building a new one, check these first.

---

## 9. Forms

**No form library today.** The canonical pattern is `SearchBar` (`components/search-bar.tsx:36-58`):

1. `useState` for field values + debounced `router.push("/search?q=...")` (300ms) + `onSubmit` with `e.preventDefault()`.
2. **Submission:** `router.push` to the server page — the server page fetches via `api.*`. No direct fetch from the form.
3. **Loading spinner:** `Loader2` with `animate-spin` while debouncing.
4. **IME composition support:** `isComposing` guard + `onCompositionEnd` re-trigger (see `search-bar.tsx:41-91`).

**Target for complex forms (when needed):** `react-hook-form` + `zod` with `@hookform/resolvers/zod`, where zod schemas **mirror the DRF serializer payloads** in `snake_case` (strict end-to-end type safety). Ask before introducing — do not add a form library for simple search/filter inputs.

---

## 10. Hooks

- File: `src/hooks/use-<feature>.ts`, first line `"use client"` if it uses client APIs.
- **Return an object** (`{ isPending, debouncedValue }`) or a plain value — never raw store slices.
- Wrap every callback in `useCallback` with correct deps; initialize state lazily (`useState(() => ...)`).
- Per-item loading state: `Set<string>` of keys with an `isLoading(key)` callback — never expose the raw `Set`.
- **No new global context/store from a hook** — URL params + `api.*` already cover the global needs.

---

## 11. Code Validation (Before Submitting)

**ALWAYS verify the code works before considering a task complete. Run from `frontend/`:**

```bash
# 1. Lint
npm run lint                 # eslint . (eslint.config.mjs)

# 2. Type check (strict: true; noEmit in tsconfig)
npx tsc --noEmit

# 3. Build (catches Server/Client boundary errors, missing exports, route issues)
npm run build

# 4. Convention checklist
#    - named exports for components; default export only for pages
#    - interface [Name]Props, never bare Props
#    - setRequestLocale present in every page when next-intl is active
#    - locale-prefixed links via i18n navigation helpers
#    - i18n keys added to BOTH messages/ar.json and messages/en.json
#    - no hardcoded user-facing strings
#    - single data path via lib/api.ts (no duplicate API_URL)
#    - envelope contract respected (handle both v1 and v2 during migration)
#    - queries use snake_case field names matching DRF serializers
```

A task is **not** done if any of these fail.

---

## 12. Critical Constraints (Do Not Violate)

1. **No Django fetch from a client component** — always through `api.*` (server path) or future BFF (`/api/...`). Never `fetch("http://...:8000/...")`.
2. **No duplicate `API_URL`** — `lib/api.ts:6` only. Any `const API_URL = process.env...` outside that file is a violation.
3. **No business logic inside future BFF route handlers** — thin delegates to `proxyWithAuth` only.
4. **The response envelope is a contract** — v1 `{count,results}` frozen, v2 `{data,meta}/{error:{code,message,details}}` target. Handle both during migration; never assume one shape.
5. **Errors handled by `code` when v2 lands**, with frontend translation table first and server `message` as fallback — never by matching message text.
6. **Every user-facing string is translated** — keys added to **both** `ar.json` and `en.json`.
7. **RTL first** — logical props (`text-start`/`text-end`, `ps`/`pe`), `dir` branching; never `left/right` for directional UI.
8. **No new global store or context** — URL params + local state only. `ProfileProvider`-style singletons only if explicitly approved.
9. **No new libraries** (state, UI kit, toast, HTTP, form, validation) without asking — `next-intl` is the approved i18n library for bilingual support.
10. **Normalization parity is mandatory** — `lib/normalize.ts:15` must stay identical to `backend/core/utils.py:14`; any change mirrors the other in the same commit.
11. **No duplicate type definitions** — all API types live in `lib/api.ts`; do not create a second `types/index.ts` without asking.
12. **Money is not applicable** — if added later, amounts are integers in smallest unit, formatted for display at the edge.

---

## 13. Known Inconsistencies & Transitional TODOs

These are existing violations / known gaps. **Do NOT copy these patterns into new code.** Fix opportunistically, one change at a time:

1. **Hardcoded Arabic strings in new pages** (`page.tsx:28-32`, `search-bar.tsx:97`) predate the `next-intl` bilingual setup — migrate them to `messages/{ar,en}.json` keys as the first i18n task.
2. **No `messages/` directory yet** — `next-intl` routing (`i18n/routing.ts`, `middleware.ts`, `[locale]/` segment) needs to be scaffolded; `app/layout.tsx:17` hardcoded `<html lang="ar" dir="rtl">` will become dynamic.
3. **`vendor/` tarballs** (`next-16.3.2.tgz`, `swc`, `sharp`) are offline workarounds for slow network — on a good network, restore `"next": "16.3.2"` in `package.json` and delete `vendor/`.
4. **`next.config.ts:7` `unoptimized: true`** — images are unoptimized; revisit when remote images are added.
5. **No frontend tests, no frontend CI** — introduce Vitest + Testing Library before relying on regression tests.
6. **No `lib/api-config.ts` single-source split** — `API_URL` lives in `lib/api.ts:6` today; if the codebase grows, extract to `lib/api-config.ts` (like `stable/frontend/AGENTS.md:3`) and import from there — ask first.
7. **Inconsistent semicolon/quote style in `lib/utils.ts` / `hooks/`** — scaffold leftovers; do not copy.
8. **No `ErrorBanner` extraction** — `bg-destructive/10 text-destructive rounded-lg p-4` is duplicated across pages — extract to `components/shared/error-banner.tsx` when it appears a third time.

---

## 14. Reference — Canonical Files

| Question | File |
| --- | --- |
| How are pages structured? | `src/app/page.tsx:16` (async server, Promise searchParams, Promise.all) |
| How does search work? | `src/components/search-bar.tsx:36-58` (debounce 300ms, composition, router.push) |
| How is the header built? | `src/components/site-header.tsx:1` ("use client", responsive toggle) |
| How does the data client work? | `src/lib/api.ts:196-268` (buildUrl, get<T>, api.* helpers) |
| How is Arabic normalized? | `src/lib/normalize.ts:7-25` (mirror of backend) |
| How are morph terms defined? | `src/lib/morphology.ts:85-283` (TERMS, getTerm, TABLE_FIELDS) |
| How is the root layout set? | `src/app/layout.tsx:15-42` (Amiri font, RTL, SiteHeader) |
| What is the backend envelope? | `../backend/AGENT.md` §5.5 + `backend/core/pagination.py:4` |
| What is the dashboard redesign plan? | `../WEBSITE_PLAN.md` §5 |

