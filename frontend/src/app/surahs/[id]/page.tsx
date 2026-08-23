import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import type { Surah } from "@/lib/api";
import { AyahView } from "@/components/ayah-view";
import { PaginationControls } from "@/components/pagination-controls";
import { api } from "@/lib/api";

const PAGE_SIZE = 50;

interface SurahPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ page?: string }>;
}

export async function generateMetadata({
  params,
}: SurahPageProps): Promise<Metadata> {
  const { id } = await params;
  const surahs = await api.surahs();
  const surah = surahs.find((s) => s.id === parseInt(id, 10));
  return {
    title: surah ? `سورة ${surah.name_ar}` : `سورة ${id}`,
    description: surah
      ? `آيات سورة ${surah.name_ar} مع تحليل صرفي لكل كلمة`
      : undefined,
  };
}

export default async function SurahPage({ params, searchParams }: SurahPageProps) {
  const { id } = await params;
  const { page: pageParam } = await searchParams;
  const surahId = parseInt(id, 10);
  if (!Number.isFinite(surahId) || surahId < 1 || surahId > 114) notFound();

  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);

  const [surahs, ayat] = await Promise.all([
    api.surahs(),
    api.ayahWords({ surah: surahId, page_size: PAGE_SIZE, page }),
  ]);

  const surah: Surah | undefined = surahs.find((s) => s.id === surahId);
  if (!surah) notFound();

  const prev: Surah | undefined = surahs.find((s) => s.id === surahId - 1);
  const next: Surah | undefined = surahs.find((s) => s.id === surahId + 1);

  return (
    <div className="space-y-6">
      <header className="space-y-2 text-center border-b pb-6">
        <h1 className="font-quran text-4xl font-bold">سورة {surah.name_ar}</h1>
        <p className="text-sm text-muted-foreground tabular-nums">
          {surah.revelation_type} · {surah.ayah_count.toLocaleString("ar-EG")} آية ·
          الجزء {surah.juz_start.toLocaleString("ar-EG")}
        </p>

        <nav className="flex items-center justify-center gap-3 pt-2 text-sm" aria-label="التنقل بين السور">
          {prev && (
            <Link href={`/surahs/${prev.id}`} className="underline-offset-2 hover:underline">
              ← {prev.name_ar}
            </Link>
          )}
          <span className="text-muted-foreground">|</span>
          <Link href="/#roots" className="underline-offset-2 hover:underline text-muted-foreground">
            كل السور
          </Link>
          <span className="text-muted-foreground">|</span>
          {next && (
            <Link href={`/surahs/${next.id}`} className="underline-offset-2 hover:underline">
              {next.name_ar} →
            </Link>
          )}
        </nav>
        <p className="text-xs text-muted-foreground pt-1">
          اضغط على أي كلمة لعرض تحليلها الصرفي.
        </p>
      </header>

      <div className="space-y-4">
        {ayat.results.map((ayah) => (
          <AyahView key={ayah.id} ayah={ayah} />
        ))}
      </div>

      <PaginationControls
        page={page}
        count={ayat.count}
        pageSize={PAGE_SIZE}
        basePath={`/surahs/${surahId}`}
      />
    </div>
  );
}
