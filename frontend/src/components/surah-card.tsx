import Link from "next/link";

import type { Surah } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getPageForSurahAyah } from "@/lib/quran-meta";

interface SurahCardProps {
  surah: Surah;
  className?: string;
}

export function SurahCard({ surah, className }: SurahCardProps) {
  const page = getPageForSurahAyah(surah.id, 1);
  const isMeccan = surah.revelation_type === "مكية";

  return (
    <Link href={`/surahs/${surah.id}`} className={cn("group block h-full", className)}>
      <Card className="h-full py-0 overflow-hidden transition-colors group-hover:border-foreground/30 group-hover:bg-accent/40 gap-0">
        <CardContent className="p-0 flex items-stretch">
          {/* رقم السورة — مزخرف */}
          <div className="flex flex-col items-center justify-center gap-1.5 px-4 py-5 bg-muted/40 border-e min-w-[72px]">
            <span className="flex items-center justify-center size-10 rounded-xl bg-background border font-bold tabular-nums text-sm">
              {surah.id.toLocaleString("ar-EG")}
            </span>
            <span className="text-[10px] text-muted-foreground tabular-nums">ص {page.toLocaleString("ar-EG")}</span>
          </div>

          <div className="flex-1 px-4 py-4 space-y-2 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-quran text-xl font-bold leading-none truncate">{surah.name_ar}</h3>
              <Badge variant={isMeccan ? "secondary" : "outline"} className="shrink-0 text-[10px] px-1.5 py-0">
                {surah.revelation_type}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground truncate" dir="ltr">
              {surah.name_en}
            </p>
            <div className="flex items-center gap-1.5 flex-wrap">
              <Badge variant="secondary" className="tabular-nums text-[11px]">
                {surah.ayah_count.toLocaleString("ar-EG")} آية
              </Badge>
              <Badge variant="outline" className="tabular-nums text-[11px]">
                الجزء {surah.juz_start.toLocaleString("ar-EG")}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export function SurahCardSkeleton() {
  return <div className="h-[110px] rounded-xl border bg-muted/30 animate-pulse" />;
}
