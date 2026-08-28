"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import type { Surah } from "@/lib/api";
import { SurahCard } from "@/components/surah-card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { stripDiacritics, normalizeAr } from "@/lib/normalize";
import { JUZ_BOUNDARIES, getSurahsForJuz, getPageRange, getPageBlocks, TOTAL_PAGES } from "@/lib/quran-meta";
import { Search, LayoutGrid, List } from "lucide-react";
import { cn } from "@/lib/utils";

interface SurahIndexClientProps {
  surahs: Surah[];
}

type RevelationFilter = "all" | "مكية" | "مدنية";
type SortBy = "id" | "ayah_count" | "name_ar";
type ViewMode = "grid" | "list";

export function SurahIndexClient({ surahs }: SurahIndexClientProps) {
  const [query, setQuery] = useState("");
  const [rev, setRev] = useState<RevelationFilter>("all");
  const [sortBy, setSortBy] = useState<SortBy>("id");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [juzQuery, setJuzQuery] = useState("");
  const [pageBlock, setPageBlock] = useState(1);

  const normalizedQuery = useMemo(() => normalizeAr(query.trim()), [query]);

  const filtered = useMemo(() => {
    let list = [...surahs];
    if (normalizedQuery) {
      list = list.filter((s) => {
        const hay = `${normalizeAr(s.name_ar)} ${normalizeAr(s.name_en)} ${s.id}`;
        const plain = stripDiacritics(hay);
        return hay.includes(normalizedQuery) || plain.includes(normalizedQuery) || String(s.id).includes(query.trim());
      });
    }
    if (rev !== "all") {
      list = list.filter((s) => s.revelation_type === rev);
    }
    if (sortBy === "ayah_count") list.sort((a, b) => b.ayah_count - a.ayah_count);
    else if (sortBy === "name_ar") list.sort((a, b) => a.name_ar.localeCompare(b.name_ar, "ar"));
    else list.sort((a, b) => a.id - b.id);
    return list;
  }, [surahs, normalizedQuery, query, rev, sortBy]);

  const juzFiltered = useMemo(() => {
    if (!juzQuery.trim()) return JUZ_BOUNDARIES;
    const q = normalizeAr(juzQuery.trim());
    return JUZ_BOUNDARIES.filter((j) => String(j.juz).includes(q));
  }, [juzQuery]);

  const pageBlocks = useMemo(() => getPageBlocks(20), []);
  const currentBlock = pageBlocks.find((b) => b.block === pageBlock) ?? pageBlocks[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="space-y-3 text-center py-2">
        <h1 className="font-quran text-3xl font-bold">فهرس السور</h1>
        <p className="text-sm text-muted-foreground">
          {surahs.length.toLocaleString("ar-EG")} سورة · تصفح مصحفي مع تقسيم الأجزاء والصفحات
        </p>
      </header>

      <Tabs defaultValue="surahs" className="w-full">
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="surahs">السور ({filtered.length.toLocaleString("ar-EG")})</TabsTrigger>
          <TabsTrigger value="juz">الأجزاء (30)</TabsTrigger>
          <TabsTrigger value="pages">الصفحات (604)</TabsTrigger>
        </TabsList>

        {/* ---- السور ---- */}
        <TabsContent value="surahs" className="space-y-4 mt-4">
          {/* أدوات فلترة */}
          <div className="flex flex-col gap-3">
            <div className="relative">
              <Search className="absolute end-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="ابحث بالاسم أو الرقم: البقرة / Baqarah / 2"
                className="pe-10"
                aria-label="بحث في السور"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1 rounded-lg border p-1">
                {(["all", "مكية", "مدنية"] as const).map((v) => (
                  <Button
                    key={v}
                    variant={rev === v ? "secondary" : "ghost"}
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => setRev(v)}
                  >
                    {v === "all" ? "الكل" : v}
                  </Button>
                ))}
              </div>

              <div className="flex items-center gap-1 rounded-lg border p-1">
                <Button
                  variant={sortBy === "id" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setSortBy("id")}
                >
                  مصحفي
                </Button>
                <Button
                  variant={sortBy === "ayah_count" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setSortBy("ayah_count")}
                >
                  الأكثر آيات
                </Button>
                <Button
                  variant={sortBy === "name_ar" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => setSortBy("name_ar")}
                >
                  أبجدي
                </Button>
              </div>

              <div className="ms-auto flex items-center gap-1 rounded-lg border p-1">
                <Button
                  variant={viewMode === "grid" ? "secondary" : "ghost"}
                  size="icon"
                  className="size-7"
                  aria-label="شبكة"
                  onClick={() => setViewMode("grid")}
                >
                  <LayoutGrid className="size-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "secondary" : "ghost"}
                  size="icon"
                  className="size-7"
                  aria-label="قائمة"
                  onClick={() => setViewMode("list")}
                >
                  <List className="size-4" />
                </Button>
              </div>
            </div>
          </div>

          {filtered.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-12">لا توجد سور مطابقة لـ «{query}»</p>
          ) : (
            <div
              className={cn(
                viewMode === "grid"
                  ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
                  : "flex flex-col gap-2"
              )}
            >
              {filtered.map((s) => (
                <SurahCard key={s.id} surah={s} />
              ))}
            </div>
          )}
        </TabsContent>

        {/* ---- الأجزاء ---- */}
        <TabsContent value="juz" className="space-y-4 mt-4">
          <div className="relative max-w-md">
            <Search className="absolute end-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            <Input
              value={juzQuery}
              onChange={(e) => setJuzQuery(e.target.value)}
              placeholder="ابحث برقم الجزء: 1 .. 30"
              className="pe-10"
              inputMode="numeric"
            />
          </div>
          <p className="text-xs text-muted-foreground">
            تقسيم الأجزاء معتمد على الحدود المصحفية القياسية (يبدأ الجزء داخل السورة غالباً). النقر ينقل لأول سورة في الجزء.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {juzFiltered.map((j) => {
              const list = getSurahsForJuz(j.juz);
              const startSurah = surahs.find((s) => s.id === j.startSurah);
              return (
                <Card key={j.juz} className="py-0 overflow-hidden">
                  <CardContent className="p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-bold">الجزء {j.juz.toLocaleString("ar-EG")}</h3>
                      <Badge variant="outline" className="tabular-nums text-xs">
                        يبدأ {startSurah?.name_ar ?? j.startSurah}:{j.startAyah.toLocaleString("ar-EG")}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {list.map((s) => (
                        <Link key={s.id} href={`/surahs/${s.id}`}>
                          <Badge variant="secondary" className="font-quran hover:bg-secondary/80">
                            {s.id}. {s.name_ar}
                          </Badge>
                        </Link>
                      ))}
                    </div>
                    <Link
                      href={`/surahs/${j.startSurah}#ayah-${j.startAyah}`}
                      className="inline-flex text-xs text-primary hover:underline underline-offset-4"
                    >
                      اذهب لبداية الجزء ←
                    </Link>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* ---- الصفحات ---- */}
        <TabsContent value="pages" className="space-y-4 mt-4">
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground leading-relaxed">
              تقسيم الصفحات 604 مُحسب حسابياً من قاعدة البيانات (10.3 آية/صفحة في المتوسط) لتوفير تنقل 604 كامل محلياً
              بدون جلب خارجي. عند إضافة `page_number` لكل آية في `ayat` سيُستبدل التقسيم بالمطابق لطبعة المدينة.
            </p>
            <div className="flex flex-wrap gap-1.5">
              {pageBlocks.map((b) => (
                <Button
                  key={b.block}
                  variant={pageBlock === b.block ? "secondary" : "outline"}
                  size="sm"
                  className="h-7 text-xs tabular-nums"
                  onClick={() => setPageBlock(b.block)}
                >
                  {b.pages[0].toLocaleString("ar-EG")}–{b.pages[b.pages.length - 1].toLocaleString("ar-EG")}
                </Button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2">
            {currentBlock.pages.map((p) => {
              const r = getPageRange(p);
              const startSurah = surahs.find((s) => s.id === r.start.surah);
              const endSurah = surahs.find((s) => s.id === r.end.surah);
              return (
                <Link
                  key={p}
                  href={`/surahs/${r.start.surah}#ayah-${r.start.ayah}`}
                  className="rounded-lg border p-3 hover:bg-accent/40 transition-colors space-y-1"
                >
                  <p className="text-xs text-muted-foreground tabular-nums">صفحة {p.toLocaleString("ar-EG")}</p>
                  <p className="font-quran text-sm leading-relaxed truncate">
                    {startSurah?.name_ar} {r.start.ayah.toLocaleString("ar-EG")}
                    {r.end.surah !== r.start.surah || r.end.ayah !== r.start.ayah
                      ? ` → ${endSurah?.name_ar} ${r.end.ayah.toLocaleString("ar-EG")}`
                      : ""}
                  </p>
                </Link>
              );
            })}
          </div>
          <p className="text-[11px] text-muted-foreground/70 text-center">
            إجمالي {TOTAL_PAGES.toLocaleString("ar-EG")} صفحة · كل صفحة ≈ 10 آيات
          </p>
        </TabsContent>
      </Tabs>
    </div>
  );
}
