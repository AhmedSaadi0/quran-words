"use client";

import { useMemo, useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, X, BookOpen, ChevronLeft } from "lucide-react";

import type { Surah } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { normalizeAr } from "@/lib/normalize";
import { JUZ_BOUNDARIES } from "@/lib/quran-meta";
import { cn } from "@/lib/utils";

interface SurahSidebarProps {
  surahs: Surah[];
  currentId: number;
}

export function SurahSidebar({ surahs, currentId }: SurahSidebarProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // close drawer on route change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- close drawer on navigation
    setOpen(false);
  }, [pathname]);

  const filtered = useMemo(() => {
    const q = normalizeAr(query.trim());
    if (!q) return surahs;
    return surahs.filter((s) => {
      const hay = `${normalizeAr(s.name_ar)} ${normalizeAr(s.name_en)} ${s.id}`;
      return hay.includes(q) || String(s.id).includes(query.trim());
    });
  }, [surahs, query]);

  // group by juz for dividers
  const juzMap = useMemo(() => {
    const m = new Map<number, number>();
    for (const j of JUZ_BOUNDARIES) m.set(j.startSurah, j.juz);
    return m;
  }, []);

  const SidebarContent = (
    <div className="flex flex-col h-full">
      <div className="p-3 space-y-3">
        <div className="flex items-center gap-2">
          <BookOpen className="size-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">فهرس السور</h2>
          <span className="ms-auto text-xs text-muted-foreground tabular-nums">{surahs.length} سورة</span>
          <Button variant="ghost" size="icon" className="size-7 lg:hidden" onClick={() => setOpen(false)} aria-label="إغلاق">
            <X className="size-4" />
          </Button>
        </div>
        <div className="relative">
          <Search className="absolute end-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground pointer-events-none" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="ابحث: البقرة / 2"
            className="h-8 pe-8 text-sm"
            aria-label="بحث في القائمة الجانبية"
          />
        </div>
      </div>
      <Separator />
      <div className="flex-1 overflow-y-auto">
        <nav className="p-2 space-y-0.5" aria-label="قائمة السور">
          {filtered.map((s) => {
            const isActive = s.id === currentId;
            const juzDivider = juzMap.get(s.id);
            return (
              <div key={s.id}>
                {juzDivider && (
                  <div className="flex items-center gap-2 py-2 px-1">
                    <Separator className="flex-1" />
                    <span className="text-[10px] text-muted-foreground whitespace-nowrap px-1 rounded bg-muted">
                      الجزء {juzDivider.toLocaleString("ar-EG")}
                    </span>
                    <Separator className="flex-1" />
                  </div>
                )}
                <Link
                  href={`/surahs/${s.id}`}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-2 py-2 text-sm transition-colors",
                    isActive ? "bg-primary text-primary-foreground" : "hover:bg-accent",
                    isActive && "font-medium"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span
                    className={cn(
                      "flex items-center justify-center size-7 rounded-md border text-xs tabular-nums shrink-0",
                      isActive ? "bg-primary-foreground text-primary border-primary-foreground/20" : "bg-background"
                    )}
                  >
                    {s.id.toLocaleString("ar-EG")}
                  </span>
                  <span className="font-quran text-[15px] truncate flex-1">{s.name_ar}</span>
                  <span className="text-[10px] opacity-70 tabular-nums hidden sm:inline">{s.ayah_count}</span>
                  {isActive && <ChevronLeft className="size-3.5 opacity-70" />}
                </Link>
              </div>
            );
          })}
          {filtered.length === 0 && <p className="text-xs text-muted-foreground text-center py-8">لا نتائج</p>}
        </nav>
      </div>
      <Separator />
      <div className="p-3">
        <Link href="/surahs" className="text-xs text-primary hover:underline underline-offset-4 flex items-center gap-1">
          عرض الفهرس الكامل <ChevronLeft className="size-3" />
        </Link>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop: sticky sidebar */}
      <aside className="hidden lg:flex w-72 shrink-0 border-e bg-background sticky top-14 h-[calc(100vh-3.5rem)] flex-col">
        {SidebarContent}
      </aside>

      {/* Mobile: toggle + drawer */}
      <div className="lg:hidden">
        <Button
          variant="outline"
          size="sm"
          className="fixed bottom-4 end-4 z-30 rounded-full shadow-lg gap-1.5"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-label="فهرس السور"
        >
          <BookOpen className="size-4" />
          الفهرس
        </Button>
        {open && (
          <div className="fixed inset-0 z-40 flex">
            <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} aria-hidden />
            <div className="relative w-80 max-w-[85vw] bg-background border-e shadow-xl flex flex-col animate-in slide-in-from-right duration-200">
              {SidebarContent}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
