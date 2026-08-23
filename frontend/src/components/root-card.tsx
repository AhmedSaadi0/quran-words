import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import type { RootItem } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function StatsCards({
  stats,
}: {
  stats: {
    surahs: number;
    ayat: number;
    words: number;
    roots: number;
    masadir: number;
    derivatives: number;
    word_occurrences: number;
  };
}) {
  const items: { label: string; value: number }[] = [
    { label: "كلمة فريدة", value: stats.words },
    { label: "موضع كلمة", value: stats.word_occurrences },
    { label: "جذر مدقق", value: stats.roots },
    { label: "مصدر", value: stats.masadir },
    { label: "مشتق", value: stats.derivatives },
    { label: "آية", value: stats.ayat },
  ];

  return (
    <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
      {items.map((it) => (
        <Card key={it.label} className="py-4 gap-1 text-center">
          <CardContent className="px-2">
            <p className="text-xl font-bold tabular-nums">
              {it.value.toLocaleString("ar-EG")}
            </p>
            <p className="text-xs text-muted-foreground mt-1">{it.label}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function RootCard({ root }: { root: RootItem }) {
  return (
    <Link href={`/roots/${encodeURIComponent(root.root)}`} className="group block h-full">
      <Card className="h-full py-4 transition-colors group-hover:border-foreground/30 group-hover:bg-accent/40">
        <CardHeader className="px-4">
          <CardTitle className="font-quran text-2xl">{root.root}</CardTitle>
          <CardDescription className="sr-only">جذر قرآني</CardDescription>
        </CardHeader>
        <CardContent className="px-4 flex flex-wrap gap-1.5">
          <Badge variant="secondary" className="tabular-nums">
            {root.masadir_count} مصدر
          </Badge>
          <Badge variant="outline" className="tabular-nums">
            {root.derivatives_count} مشتق
          </Badge>
          <ArrowLeft className="size-4 ms-auto self-center opacity-0 transition-opacity group-hover:opacity-60" />
        </CardContent>
      </Card>
    </Link>
  );
}
