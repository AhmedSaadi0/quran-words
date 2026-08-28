"use client";

import { useEffect, useState, useCallback } from "react";

const STORAGE_KEY = "quran-reading-progress";
const FONT_KEY = "quran-font-size";

interface ReadingProgress {
  surah: number;
  ayah: number;
  page: number;
  updatedAt: string;
}

export function useReadingProgress(surahId: number, page: number) {
  const [progress, setProgress] = useState<ReadingProgress | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrate from localStorage
      if (raw) setProgress(JSON.parse(raw));
    } catch {}
  }, []);

  const save = useCallback(
    (ayah: number) => {
      const p: ReadingProgress = { surah: surahId, ayah, page, updatedAt: new Date().toISOString() };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(p));
        setProgress(p);
      } catch {}
    },
    [surahId, page]
  );

  // auto-save on mount (first visible ayah)
  useEffect(() => {
    const firstAyah = (page - 1) * 20 + 1;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- save progress on page change
    save(firstAyah);
  }, [page, save]);

  return { progress, save };
}

export function useFontSize() {
  const [size, setSize] = useState<number>(18);

  useEffect(() => {
    try {
      localStorage.setItem(FONT_KEY, String(size));
    } catch {}
  }, [size]);

  // hydrate from storage on mount (client) — keep initial 18 for SSR hydration match
  useEffect(() => {
    try {
      const v = localStorage.getItem(FONT_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- hydrate font size
      if (v) setSize(Math.min(32, Math.max(14, parseInt(v, 10) || 18)));
    } catch {}
  }, []);

  return { size, setSize };
}
