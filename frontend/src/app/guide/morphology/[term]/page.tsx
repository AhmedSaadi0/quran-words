import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import {
  FIELDS,
  TERMS,
  getTermByKey,
} from "@/lib/morphology";

interface TermPageProps {
  params: Promise<{ term: string }>;
}

function findTerm(key: string) {
  return getTermByKey(key);
}

export function generateStaticParams() {
  return TERMS.map((t) => ({ term: t.key }));
}

export async function generateMetadata({
  params,
}: TermPageProps): Promise<Metadata> {
  const { term } = await params;
  const doc = findTerm(term);
  return {
    title: doc ? `${doc.label} — ${FIELDS[doc.field].title}` : "مصطلح غير معروف",
    description: doc?.short,
  };
}

export default async function TermPage({ params }: TermPageProps) {
  const { term } = await params;
  const doc = findTerm(term);
  if (!doc) notFound();

  const fieldMeta = FIELDS[doc.field];
  const siblings = TERMS.filter(
    (t) => t.field === doc.field && t.key !== doc.key
  );

  return (
    <div className="space-y-6 max-w-3xl">
      <nav className="text-sm text-muted-foreground">
        <Link href="/guide/morphology" className="hover:text-foreground underline-offset-4 hover:underline">
          دليل المصطلحات
        </Link>
        <span className="mx-2">/</span>
        <span>{fieldMeta.title}</span>
      </nav>

      <header className="space-y-2">
        <div className="flex items-baseline gap-3">
          <h1 className="text-3xl font-bold">{doc.label}</h1>
          <code dir="ltr" className="text-xs bg-muted px-2 py-0.5 rounded font-mono">
            {doc.value}
          </code>
        </div>
        <p className="font-quran text-xl leading-relaxed text-muted-foreground">
          {doc.short}
        </p>
      </header>

      <section className="rounded-xl border p-5 space-y-3 leading-relaxed">
        <h2 className="font-semibold">الشرح</h2>
        <p>{doc.explanation}</p>
      </section>

      {doc.example && (
        <section className="rounded-xl border bg-accent/30 p-5 space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground">مثال قرآني</h2>
          <p className="font-quran text-3xl leading-snug">{doc.example.text}</p>
          <Link
            href={`/surahs/${doc.example.surah}#ayah-${doc.example.ayah}`}
            className="inline-block text-xs underline underline-offset-4 text-muted-foreground hover:text-foreground"
          >
            {doc.example.ref} ←
          </Link>
        </section>
      )}

      {siblings.length > 0 && (
        <section className="space-y-2 pt-2 border-t">
          <h2 className="text-sm font-semibold text-muted-foreground">
            مصطلحات من نفس الباب: {fieldMeta.title}
          </h2>
          <div className="flex flex-wrap gap-2">
            {siblings.map((s) => (
              <Link
                key={s.key}
                href={`/guide/morphology/${s.key}`}
                className="rounded-md border px-3 py-1.5 text-sm hover:bg-accent/40 transition-colors"
              >
                {s.label}
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
