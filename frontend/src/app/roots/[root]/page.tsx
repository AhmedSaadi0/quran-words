import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import type { RootItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MasdarList, DerivativeGrid, MeaningList } from "@/components/masdar-list";
import { PaginationControls } from "@/components/pagination-controls";
import { RootAyahList } from "@/components/root-ayah-list";
import { api } from "@/lib/api";

interface RootPageProps {
  params: Promise<{ root: string }>;
  searchParams: Promise<{ page?: string; tab?: string }>;
}

export async function generateMetadata({
  params,
}: RootPageProps): Promise<Metadata> {
  const { root } = await params;
  return { title: `الجذر ${decodeURIComponent(root)}` };
}

export default async function RootPage({ params, searchParams }: RootPageProps) {
  const { root: rawRoot } = await params;
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);
  const rootText = decodeURIComponent(rawRoot).trim();

  // Resolve the root id by exact text match first
  const found = await api.roots({ q: rootText });
  const match =
    found.results.find((r: RootItem) => r.root === rootText) ?? found.results[0];

  if (!match) notFound();

  const [meanings, masadir, derivatives, words, ayatFirst] = await Promise.all([
    api.meanings({ root_id: match.id }),
    api.masadir({ root: rootText }),
    api.derivatives({ root: rootText }),
    api.words({ root: rootText, page }),
    api.ayahWords({ root: rootText, page_size: 1000 }),
  ]);

  // جلب كل الآيات إذا كان العدد أكبر من page_size (المستخدم طلب كل الآيات)
  let ayat = ayatFirst;
  if (ayatFirst.count > ayatFirst.results.length) {
    const totalPages = Math.ceil(ayatFirst.count / 1000);
    const extraPages = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, i) =>
        api.ayahWords({ root: rootText, page: i + 2, page_size: 1000 })
      )
    );
    ayat = {
      ...ayatFirst,
      results: [...ayatFirst.results, ...extraPages.flatMap((p) => p.results)],
    };
  }

  const quranicCount = derivatives.results.filter((d) => d.is_quranic).length;

  return (
    <div className="space-y-6" dir="rtl">
      <header className="space-y-2">
        <div className="flex items-baseline gap-3">
          <h1 className="font-quran text-5xl font-bold">{match.root}</h1>
          <Badge variant="secondary">جذر</Badge>
        </div>
        {match.gloss_ar && (
          <div className="rounded-xl border bg-accent/30 px-5 py-4 space-y-1.5">
            <p className="text-xs font-medium text-muted-foreground">
              المعنى المختصر
            </p>
            <p className="font-quran text-2xl leading-relaxed">{match.gloss_ar}</p>
            {match.gloss_en && (
              <p dir="ltr" className="text-sm text-muted-foreground text-left">
                {match.gloss_en}
              </p>
            )}
            {match.gloss_source && (
              <p className="text-[11px] text-muted-foreground/70">
                المصدر: {match.gloss_source}
              </p>
            )}
          </div>
        )}
        <p className="text-sm text-muted-foreground tabular-nums">
          {words.count.toLocaleString("ar-EG")} كلمة ·{" "}
          {masadir.count.toLocaleString("ar-EG")} مصدر ·{" "}
          {derivatives.count.toLocaleString("ar-EG")} مشتق (
          {quranicCount.toLocaleString("ar-EG")} قرآني)
        </p>
      </header>

      <Tabs dir="rtl" defaultValue="meanings" className="gap-4">
        <TabsList dir="rtl" className="justify-start">
          <TabsTrigger value="meanings">
            المعاني{" "}
            <span className="tabular-nums text-muted-foreground">
              {meanings.count}
            </span>
          </TabsTrigger>
          <TabsTrigger value="masadir">
            المصادر{" "}
            <span className="tabular-nums text-muted-foreground">
              {masadir.count}
            </span>
          </TabsTrigger>
          <TabsTrigger value="derivatives">
            المشتقات{" "}
            <span className="tabular-nums text-muted-foreground">
              {derivatives.count}
            </span>
          </TabsTrigger>
          <TabsTrigger value="words">
            الكلمات{" "}
            <span className="tabular-nums text-muted-foreground">
              {words.count}
            </span>
          </TabsTrigger>
          <TabsTrigger value="ayat">
            الآيات{" "}
            <span className="tabular-nums text-muted-foreground">
              {ayat.count}
            </span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="meanings" dir="rtl" className="space-y-3 text-right">
          <MeaningList meanings={meanings.results} />
        </TabsContent>

        <TabsContent value="masadir" dir="rtl" className="space-y-3 text-right">
          <MasdarList masadir={masadir.results} />
        </TabsContent>

        <TabsContent value="derivatives" dir="rtl" className="space-y-3 text-right">
          <DerivativeGrid derivatives={derivatives.results} />
        </TabsContent>

        <TabsContent value="words" dir="rtl" className="space-y-4 text-right">
          <WordsTable
            words={words.results.map((w) => ({
              id: w.id,
              text: w.text,
              translation: w.translation,
              transliteration: w.transliteration,
            }))}
          />
          <PaginationControls
            page={page}
            count={words.count}
            pageSize={20}
            basePath={`/roots/${encodeURIComponent(rootText)}`}
          />
        </TabsContent>

        <TabsContent value="ayat" dir="rtl" className="space-y-3 text-right">
          <RootAyahList ayat={ayat.results} rootText={rootText} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function WordsTable({
  words,
}: {
  words: {
    id: number;
    text: string;
    translation: string | null;
    transliteration: string | null;
  }[];
}) {
  if (!words.length) {
    return <p className="text-sm text-muted-foreground">لا توجد كلمات.</p>;
  }
  return (
    <ol className="divide-y rounded-xl border">
      {words.map((w, i) => (
        <li key={w.id}>
          <Link
            href={`/words/${w.id}`}
            className="flex items-center gap-4 px-4 py-3 hover:bg-accent/40 transition-colors"
          >
            <span className="text-xs text-muted-foreground tabular-nums w-6">
              {(i + 1).toLocaleString("ar-EG")}
            </span>
            <span className="font-quran text-2xl">{w.text}</span>
            {w.transliteration && (
              <span dir="ltr" className="text-xs text-muted-foreground italic hidden sm:inline">
                {w.transliteration}
              </span>
            )}
            <span className="ms-auto text-xs text-muted-foreground truncate max-w-[45%]">
              {w.translation}
            </span>
          </Link>
        </li>
      ))}
    </ol>
  );
}
