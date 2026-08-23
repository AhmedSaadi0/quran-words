"use client";

import { useMemo } from "react";
import Link from "next/link";

import type { AyahWordEntry, Morphology } from "@/lib/api";
import { TABLE_FIELDS, type FieldKey } from "@/lib/morphology";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { TermValue } from "@/components/term-value";

interface Segment {
  segment?: string;
  translation?: string;
}

function parseSegments(raw: string | null): Segment[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Segment[]) : [];
  } catch {
    return [];
  }
}

function MorphDetails({ morph }: { morph: Morphology }) {
  const segments = useMemo(() => parseSegments(morph.segments), [morph.segments]);

  const record = morph as unknown as Record<string, unknown>;
  const rows: [string, FieldKey, string][] = [];
  for (const { field, label } of TABLE_FIELDS) {
    const v = record[field];
    if (v !== null && v !== undefined && v !== "") {
      rows.push([label, field, String(v)]);
    }
  }

  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-2">
        {morph.lemma_text && (
          <span className="font-quran text-2xl">{morph.lemma_text}</span>
        )}
        {morph.root_text && (
          <Link
            href={`/roots/${encodeURIComponent(morph.root_text)}`}
            className="inline-flex"
          >
            <Badge variant="secondary" className="font-quran text-base">
              {morph.root_text}
            </Badge>
          </Link>
        )}
      </div>

      {morph.root_gloss && (
        <p className="rounded-md bg-accent/40 px-2 py-1.5 font-quran text-base leading-relaxed">
          {morph.root_gloss}
        </p>
      )}

      {segments.length > 0 && (
        <ul className="space-y-1 rounded-md bg-muted/50 p-2">
          {segments.map((s, i) => (
            <li key={i} className="flex justify-between gap-4">
              <span className="font-quran text-base">{s.segment}</span>
              <span dir="ltr" className="text-xs text-muted-foreground text-left">
                {s.translation}
              </span>
            </li>
          ))}
        </ul>
      )}

      {rows.length > 0 && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
          {rows.map(([label, field, value]) => (
            <div key={label + value} className="contents">
              <dt className="text-muted-foreground">{label}</dt>
              <dd>
                <TermValue field={field} value={value} />
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}

export function MorphPopover({
  entry,
  wordId,
}: {
  entry: AyahWordEntry;
  wordId: number;
}) {
  const morph = entry.morphology;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="font-quran text-2xl leading-relaxed px-0.5 rounded hover:bg-accent transition-colors cursor-pointer"
        >
          {entry.word.text}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80" dir="rtl">
        {morph ? (
          <MorphDetails morph={morph} />
        ) : (
          <p className="font-quran text-xl">{entry.word.text}</p>
        )}
        <Link
          href={`/words/${wordId}`}
          className="mt-3 inline-block text-xs underline underline-offset-2 text-muted-foreground hover:text-foreground"
        >
          صفحة الكلمة ←
        </Link>
      </PopoverContent>
    </Popover>
  );
}
