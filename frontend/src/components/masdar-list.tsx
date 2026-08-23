import Link from "next/link";

import type { Masdar, Derivative } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function MasdarList({ masadir }: { masadir: Masdar[] }) {
  if (!masadir.length) {
    return <p className="text-sm text-muted-foreground">لا توجد مصادر.</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {masadir.map((m) => (
        <Link
          key={m.id}
          href={`/search?q=${encodeURIComponent(m.masdar_plain)}&type=masdar`}
          className="group block"
        >
          <Card className="py-4 transition-colors group-hover:bg-accent/40">
            <CardHeader className="px-4 pb-1">
              <CardTitle className="font-quran text-xl flex items-center gap-2">
                {m.masdar_ar}
                {m.is_attested && (
                  <Badge variant="gold">موثّق قرآنياً</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              {m.form && <Badge variant="outline">{m.form}</Badge>}
              {m.pattern && <span>{m.pattern}</span>}
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

export function DerivativeGrid({
  derivatives,
  quranicOnly = false,
}: {
  derivatives: Derivative[];
  quranicOnly?: boolean;
}) {
  const list = quranicOnly
    ? derivatives.filter((d) => d.is_quranic)
    : derivatives;

  if (!list.length) {
    return <p className="text-sm text-muted-foreground">لا توجد مشتقات.</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {list.map((d) => (
        <Link
          key={d.id}
          href={`/words/${d.example_word}`}
          className="group block"
          aria-disabled={!d.example_word}
        >
          <Card className="h-full py-4 transition-colors group-hover:bg-accent/40">
            <CardContent className="px-4 space-y-1.5">
              <p className="font-quran text-xl">
                {d.form_ar}
                {d.is_quranic && (
                  <Badge variant="gold" className="ms-2 align-middle">
                    قرآني
                  </Badge>
                )}
              </p>
              <p className="text-xs text-muted-foreground">{d.derivative_type}</p>
              <p className="text-xs text-muted-foreground flex flex-wrap gap-x-2">
                <span>{d.pattern}</span>
                {d.example_word_text && (
                  <span className="font-quran text-sm">
                    مثال: {d.example_word_text}
                  </span>
                )}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

export function MeaningList({
  meanings,
}: {
  meanings: { id: number; definition: string | null; book_name: string | null; source_url: string | null }[];
}) {
  if (!meanings.length) {
    return <p className="text-sm text-muted-foreground">لا توجد معاني.</p>;
  }
  return (
    <ul className="space-y-4">
      {meanings.map((m) => (
        <li key={m.id} className="space-y-1">
          {m.book_name && (
            <p className="text-xs font-medium text-muted-foreground">
              {m.book_name}
            </p>
          )}
          <p className="leading-relaxed">{m.definition}</p>
          {m.source_url && (
            <a
              href={m.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-muted-foreground underline underline-offset-2"
            >
              المصدر
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}
