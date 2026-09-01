import type { Metadata } from "next";
import { notFound } from "next/navigation";

import type { Surah } from "@/lib/api";
import { SurahSidebar } from "@/components/surah-sidebar";
import { SurahViewClient } from "@/components/surah-view-client";
import { api } from "@/lib/api";
import { SURAH_PAGES } from "@/lib/pages.generated";

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

  const mushafPages = SURAH_PAGES[surahId] ?? [];
  const rawPage = parseInt(pageParam ?? "", 10);
  const page =
    mushafPages.length > 0
      ? mushafPages.includes(rawPage)
        ? rawPage
        : mushafPages[0]
      : Math.max(1, parseInt(pageParam ?? "1", 10) || 1);

  const surahs = await api.surahs();
  // Direct ORM: bypass offset pagination, fetch exact Mushaf page for this surah
  // Defensive: backend returns AyahWithWords[] direct; handle both array and Paginated shapes
  const rawList = (await api.mushafAyahWords({ surah: surahId, page_number: page })) as unknown;
  const ayatList: import("@/lib/api").AyahWithWords[] = Array.isArray(rawList)
    ? (rawList as import("@/lib/api").AyahWithWords[])
    : Array.isArray((rawList as { results?: unknown }).results)
      ? ((rawList as { results: import("@/lib/api").AyahWithWords[] }).results)
      : [];
  const ayat = { results: ayatList, count: mushafPages.length };
  const pageSize = 1;

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
          pageSize={pageSize}
          surahId={surahId}
          prev={prev}
          next={next}
        />
      </div>
    </div>
  );
}
