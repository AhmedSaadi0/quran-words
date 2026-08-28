import type { Metadata } from "next";

import { SurahIndexClient } from "@/components/surah-index-client";
import { api } from "@/lib/api";

export const metadata: Metadata = {
  title: "فهرس السور — 114 سورة",
  description: "فهرس السور كامل مع تقسيم الأجزاء (30) والصفحات (604) — تصفح مصحفي للقرآن الكريم",
};

export default async function SurahsIndexPage() {
  const surahs = await api.surahs();

  return <SurahIndexClient surahs={surahs} />;
}
