"use client";

import { useEffect } from "react";
import Link from "next/link";

import type { Surah, AyahWithWords } from "@/lib/api";
import { AyahView } from "@/components/ayah-view";
import { SurahJump } from "@/components/surah-jump";
import { PaginationControls } from "@/components/pagination-controls";
import { Button } from "@/components/ui/button";
import { useFontSize, useReadingProgress } from "@/hooks/use-reading-progress";
import { Minus, Plus } from "lucide-react";

interface SurahViewClientProps {
  surah: Surah;
  ayat: { results: AyahWithWords[]; count: number };
  page: number;
  pageSize: number;
  surahId: number;
  prev?: Surah;
  next?: Surah;
}

export function SurahViewClient({ surah, ayat, page, pageSize, surahId, prev, next }: SurahViewClientProps) {
  const { size, setSize } = useFontSize();
  const { save } = useReadingProgress(surahId, page);
  const totalPages = Math.max(1, Math.ceil(surah.ayah_count / pageSize));

  // keyboard navigation: ArrowLeft -> next, ArrowRight -> prev (RTL)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft" && next) {
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- intentional full nav
        window.location.href = `/surahs/${next.id}`;
      } else if (e.key === "ArrowRight" && prev) {
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- intentional full nav
        window.location.href = `/surahs/${prev.id}`;
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next]);

  // highlight hash on load
  useEffect(() => {
    const hash = window.location.hash;
    if (hash) {
      const el = document.querySelector(hash);
      if (el) {
        setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "center" }), 100);
        el.classList.add("ring-2", "ring-primary", "ring-offset-2");
        setTimeout(() => el.classList.remove("ring-2", "ring-primary", "ring-offset-2"), 1800);
        // save reading progress for that ayah
        const m = hash.match(/ayah-(\d+)/);
        if (m) save(parseInt(m[1], 10));
      }
    }
  }, [save]);

  // observe visible ayat to save progress
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const id = entry.target.id; // ayah-N
            const m = id.match(/ayah-(\d+)/);
            if (m) save(parseInt(m[1], 10));
          }
        }
      },
      { threshold: 0.5 }
    );
    const els = document.querySelectorAll("[id^='ayah-']");
    els.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [ayat.results, save]);

  const showBasmala = surahId !== 1 && surahId !== 9;

  return (
    <div className="space-y-6">
      <header className="space-y-3 text-center border-b pb-6">
        <h1 className="font-quran text-4xl font-bold">سورة {surah.name_ar}</h1>
        <p className="text-sm text-muted-foreground tabular-nums">
          {surah.revelation_type} · {surah.ayah_count.toLocaleString("ar-EG")} آية · الجزء{" "}
          {surah.juz_start.toLocaleString("ar-EG")}
        </p>

        <nav className="flex items-center justify-center gap-3 pt-2 text-sm" aria-label="التنقل بين السور">
          {prev ? (
            <Link href={`/surahs/${prev.id}`} className="underline-offset-2 hover:underline">
              ← {prev.name_ar}
            </Link>
          ) : (
            <span className="text-muted-foreground/50">← لا يوجد</span>
          )}
          <span className="text-muted-foreground">|</span>
          <Link href="/surahs" className="underline-offset-2 hover:underline text-muted-foreground">
            كل السور
          </Link>
          <span className="text-muted-foreground">|</span>
          {next ? (
            <Link href={`/surahs/${next.id}`} className="underline-offset-2 hover:underline">
              {next.name_ar} →
            </Link>
          ) : (
            <span className="text-muted-foreground/50">لا يوجد →</span>
          )}
        </nav>

        {showBasmala && (
          <p className="font-quran pt-3 text-muted-foreground" style={{ fontSize: `${Math.min(28, size + 2)}px` }}>
            بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
          </p>
        )}

        <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
          <SurahJump surahId={surahId} ayahCount={surah.ayah_count} currentPage={page} totalPages={totalPages} />
          <div className="flex items-center gap-1 rounded-lg border p-1">
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => setSize((s) => Math.max(14, s - 1))}
              aria-label="تصغير الخط"
            >
              <Minus className="size-3.5" />
            </Button>
            <span className="text-xs tabular-nums min-w-[3ch] text-center">{size}</span>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => setSize((s) => Math.min(32, s + 1))}
              aria-label="تكبير الخط"
            >
              <Plus className="size-3.5" />
            </Button>
          </div>
        </div>

        <p className="text-xs text-muted-foreground pt-1">اضغط على أي كلمة لعرض تحليلها الصرفي · استخدم ← → للتنقل بين السور</p>
      </header>

      <div className="space-y-4" style={{ fontSize: `${size}px` } as React.CSSProperties}>
        {ayat.results.map((ayah) => (
          <AyahView key={ayah.id} ayah={ayah} />
        ))}
      </div>

      <PaginationControls page={page} count={ayat.count} pageSize={pageSize} basePath={`/surahs/${surahId}`} />
    </div>
  );
}
