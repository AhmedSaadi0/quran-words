import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import type { Morphology } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { MasdarList, DerivativeGrid, MeaningList } from "@/components/masdar-list";
import { ReportIssueCard } from "@/components/report-issue-button";
import { TermValue } from "@/components/term-value";
import { TABLE_FIELDS, type FieldKey } from "@/lib/morphology";
import { api } from "@/lib/api";
import { formatAiDate } from "@/lib/utils";

interface WordPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: WordPageProps): Promise<Metadata> {
  const { id } = await params;
  const detail = await api.wordDetail(parseInt(id, 10)).catch(() => null);
  return { title: detail ? detail.word.text : `كلمة ${id}` };
}

const MORPH_ROWS = TABLE_FIELDS;

function MorphologyTable({ morph }: { morph: Morphology }) {
  const record = morph as unknown as Record<string, unknown>;
  const entries: [string, FieldKey, string][] = [];
  for (const { field, label } of MORPH_ROWS) {
    const v = record[field];
    if (v !== null && v !== undefined && v !== "") {
      entries.push([label, field, String(v)]);
    }
  }

  if (!entries.length) return null;

  return (
    <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2 text-sm">
      {entries.map(([label, field, value]) => (
        <div key={label + value} className="flex justify-between gap-2 border-b pb-1">
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="font-medium">
            <TermValue field={field} value={value} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

export default async function WordPage({ params }: WordPageProps) {
  const { id } = await params;
  const wordId = parseInt(id, 10);
  if (!Number.isFinite(wordId)) notFound();

  let detail;
  try {
    detail = await api.wordDetail(wordId);
  } catch {
    notFound();
  }

  const { word, root, occurrences, occurrences_count, masadir, derivatives, meanings } =
    detail;

  const firstMorph = occurrences.find((o) => o.morphology)?.morphology ?? null;

  return (
    <div className="space-y-8">
      <header className="space-y-3 text-center py-4">
        <p className="font-quran text-6xl leading-snug">{word.text}</p>
        <div className="space-y-1">
          {word.transliteration && (
            <p dir="ltr" className="text-sm italic text-muted-foreground">
              {word.transliteration}
            </p>
          )}
          {word.translation && (
            <p dir="ltr" className="text-sm text-muted-foreground">
              {word.translation}
            </p>
          )}
        </div>
        {root && (
          <div className="flex items-center justify-center gap-2 pt-2">
            <span className="text-xs text-muted-foreground">الجذر:</span>
            <Link href={`/roots/${encodeURIComponent(root.root)}`}>
              <Badge variant="secondary" className="font-quran text-lg px-3 py-1">
                {root.root}
              </Badge>
            </Link>
          </div>
        )}
        {root && (
          <div className="mx-auto max-w-xl rounded-lg border bg-accent/30 px-4 py-3 space-y-1.5 mt-2">
            <p className="text-[11px] font-medium text-muted-foreground">
              الملخص الذكي للجذر {root.root}
            </p>
            {root.ai_summary_ar ? (
              <>
                <p className="font-quran text-xl leading-relaxed">{root.ai_summary_ar}</p>
                <p className="text-[11px] text-muted-foreground/70 flex flex-wrap items-center justify-center gap-x-2 gap-y-1">
                  <span>مولّد بالذكاء الاصطناعي</span>
                  {root.ai_summary_model && (
                    <>
                      <span>·</span>
                      <span>{root.ai_summary_model}</span>
                    </>
                  )}
                  {formatAiDate(root.ai_summary_generated_at) && (
                    <>
                      <span>·</span>
                      <span className="tabular-nums">{formatAiDate(root.ai_summary_generated_at)}</span>
                    </>
                  )}
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground/70 italic leading-relaxed">
                الملخص الذكي لهذا الجذر غير متوفر حالياً — قاعدة البيانات قيد التحديث وسيُضاف قريباً.
              </p>
            )}
          </div>
        )}
        {root && (
          <div className="mx-auto max-w-xl">
            <ReportIssueCard rootText={root.root} rootId={root.id} />
          </div>
        )}
        <p className="text-sm text-muted-foreground tabular-nums">
          وردت {occurrences_count.toLocaleString("ar-EG")} مرة
        </p>
      </header>

      {firstMorph && (
        <Card>
          <CardHeader>
            <CardTitle>التحليل الصرفي</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <MorphologyTable morph={firstMorph} />
          </CardContent>
        </Card>
      )}

      {masadir.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">مصادر الجذر</h2>
          <MasdarList masadir={masadir} />
        </section>
      )}

      {derivatives.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">مشتقات الجذر</h2>
          <DerivativeGrid derivatives={derivatives} />
        </section>
      )}

      {meanings.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">معاني الجذر</h2>
          <Card className="py-5">
            <CardContent className="px-6">
              <MeaningList meanings={meanings} />
            </CardContent>
          </Card>
        </section>
      )}
      {meanings.length === 0 && root && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">معاني الجذر</h2>
          <p className="text-sm text-muted-foreground">لا توجد معاني.</p>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">
          مواضع الورود{" "}
          <span className="text-sm font-normal text-muted-foreground tabular-nums">
            ({Math.min(occurrences.length, occurrences_count).toLocaleString("ar-EG")}{" "}
            من {occurrences_count.toLocaleString("ar-EG")})
          </span>
        </h2>
        <ul className="divide-y rounded-xl border">
          {occurrences.map((o) => (
            <li key={o.word_ayah_id} className="px-4 py-3 space-y-1.5">
              <div className="flex items-center gap-3">
                <Link
                  href={`/surahs/${o.ayah.surah}#ayah-${o.ayah.ayah}`}
                  className="text-xs text-muted-foreground hover:text-foreground tabular-nums"
                >
                  {o.ayah.surah_name} : {o.ayah.ayah}
                  {o.location && ` (${o.location})`}
                </Link>
              </div>
              <p className="font-quran text-xl leading-relaxed">
                {o.ayah.text_uthmani}
              </p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
