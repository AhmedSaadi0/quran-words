import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import type { RootItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MasdarList, DerivativeGrid, MeaningList } from "@/components/masdar-list";
import { PaginationControls } from "@/components/pagination-controls";
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

  const [meanings, masadir, derivatives, words] = await Promise.all([
    api.meanings({ root_id: match.id }),
    api.masadir({ root: rootText }),
    api.derivatives({ root: rootText }),
    api.words({ root: rootText, page }),
  ]);

  const quranicCount = derivatives.results.filter((d) => d.is_quranic).length;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex items-baseline gap-3">
          <h1 className="font-quran text-5xl font-bold">{match.root}</h1>
          <Badge variant="secondary">جذر</Badge>
        </div>
        <p className="text-sm text-muted-foreground tabular-nums">
          {words.count.toLocaleString("ar-EG")} كلمة ·{" "}
          {masadir.count.toLocaleString("ar-EG")} مصدر ·{" "}
          {derivatives.count.toLocaleString("ar-EG")} مشتق (
          {quranicCount.toLocaleString("ar-EG")} قرآني)
        </p>
      </header>

      <Tabs defaultValue="masadir" className="gap-4">
        <TabsList>
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
          <TabsTrigger value="meanings">
            المعاني{" "}
            <span className="tabular-nums text-muted-foreground">
              {meanings.count}
            </span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="masadir" className="space-y-3">
          <MasdarList masadir={masadir.results} />
        </TabsContent>

        <TabsContent value="derivatives" className="space-y-3">
          <DerivativeGrid derivatives={derivatives.results} />
        </TabsContent>

        <TabsContent value="words" className="space-y-4">
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

        <TabsContent value="meanings">
          <MeaningList meanings={meanings.results} />
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
