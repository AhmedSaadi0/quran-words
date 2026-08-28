"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

interface SurahJumpProps {
  surahId: number;
  ayahCount: number;
  currentPage: number;
  totalPages: number;
}

export function SurahJump({ surahId, ayahCount, currentPage, totalPages }: SurahJumpProps) {
  const router = useRouter();
  const [ayah, setAyah] = useState("");

  function go() {
    const n = parseInt(ayah, 10);
    if (!Number.isFinite(n) || n < 1 || n > ayahCount) return;
    // compute page containing ayah n (20 per page)
    const targetPage = Math.ceil(n / 20);
    if (targetPage !== currentPage) {
      router.push(`/surahs/${surahId}?page=${targetPage}#ayah-${n}`);
    } else {
      // same page: just hash nav
      const el = document.getElementById(`ayah-${n}`);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
      // update hash
      history.replaceState(null, "", `#ayah-${n}`);
      // highlight
      el?.classList.add("ring-2", "ring-primary", "ring-offset-2");
      setTimeout(() => el?.classList.remove("ring-2", "ring-primary", "ring-offset-2"), 1500);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted-foreground whitespace-nowrap">اذهب لآية</span>
        <Input
          value={ayah}
          onChange={(e) => setAyah(e.target.value.replace(/[^\d٠-٩]/g, ""))}
          onKeyDown={(e) => e.key === "Enter" && go()}
          placeholder={`1–${ayahCount.toLocaleString("ar-EG")}`}
          className="h-8 w-28 text-center tabular-nums"
          inputMode="numeric"
          aria-label="رقم الآية"
        />
        <Button size="sm" className="h-8 gap-1" onClick={go}>
          اذهب <ArrowLeft className="size-3.5" />
        </Button>
      </div>
      {totalPages > 1 && (
        <span className="text-xs text-muted-foreground tabular-nums hidden sm:inline">
          صفحة {currentPage.toLocaleString("ar-EG")} من {totalPages.toLocaleString("ar-EG")}
        </span>
      )}
    </div>
  );
}
