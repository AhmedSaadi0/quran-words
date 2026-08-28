import type { Metadata } from "next";
import { notFound } from "next/navigation";

import type { Surah } from "@/lib/api";
import { SurahSidebar } from "@/components/surah-sidebar";
import { SurahViewClient } from "@/components/surah-view-client";
import { api } from "@/lib/api";

// 20 avoids Next.js 2MB Data Cache limit (50 with morphology is ~2.2MB -> cache write fails)
const PAGE_SIZE = 20;

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
      ? `آيات سورة ${surah.name_ar} مع تحليل صرفي لكل كلمة — الجزء ${surah.juz_start} · ${surah.ayah_count} آية`
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
    <div className="flex gap-6 -mx-4">
      <SurahSidebar surahs={surahs} currentId={surahId} />
      <div className="flex-1 min-w-0 px-4">
        <SurahViewClient
          surah={surah}
          ayat={ayat}
          page={page}
          pageSize={PAGE_SIZE}
          surahId={surahId}
          prev={prev}
          next={next}
        />
      </div>
    </div>
  );
}
