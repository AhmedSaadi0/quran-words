"use client";

import { useMemo } from "react";
import Link from "next/link";

import type { AyahWordEntry, Morphology } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

const POS_AR: Record<string, string> = {
  N: "اسم",
  V: "فعل",
  P: "حرف جر",
  PRON: "ضمير",
  "DEM": "اسم إشارة",
  REL: "اسم موصول",
  T: "ظرف زمان",
  L: "ظرف مكان",
  INL: "أداة استئناف",
  INTG: "أداة استفهام",
  NEG: "أداة نفي",
  IMPV: "أداة نهي",
  ACC: "أداة نصب",
  SUB: "حرف مصدري",
  PREP: "حرف جر",
  CONJ: "حرف عطف",
  PART: "أداة",
  PN: "علم",
};

const CASE_AR: Record<string, string> = {
  NOM: "مرفوع",
  ACC: "منصوب",
  GEN: "مجرور",
};

const PERSON_AR: Record<string, string> = {
  "1": "المتكلم",
  "2": "المخاطب",
  "3": "الغائب",
};

const GENDER_AR: Record<string, string> = {
  M: "مذكر",
  F: "مؤنث",
};

const NUMBER_AR: Record<string, string> = {
  S: "مفرد",
  D: "مثنى",
  P: "جمع",
};

function ar(dict: Record<string, string>, key: string | null | undefined) {
  if (!key) return null;
  return dict[key] ?? key;
}

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
  const rows: [string, string][] = [];
  const pos = ar(POS_AR, morph.pos);
  if (pos) rows.push(["نوع الكلمة", pos]);
  if (morph.form) rows.push(["الباب", `الفعل ${morph.form}`]);
  const person = ar(PERSON_AR, morph.person);
  if (person) rows.push(["الضمير", person]);
  const gender = ar(GENDER_AR, morph.gender);
  if (gender) rows.push(["الجنس", gender]);
  const number = ar(NUMBER_AR, morph.number);
  if (number) rows.push(["العدد", number]);
  const kase = ar(CASE_AR, morph.grammatical_case);
  if (kase) rows.push(["الحالة الإعرابية", kase]);
  if (morph.state === "definite") rows.push(["التعريف", "معرفة"]);
  if (morph.state === "indefinite") rows.push(["التعريف", "نكرة"]);
  if (morph.derivation) rows.push(["الاشتقاق", morph.derivation]);

  const segments = useMemo(() => parseSegments(morph.segments), [morph.segments]);

  return (
    <div className="space-y-3 text-sm">
      <div className="flex items-center gap-2">
        <span className="font-quran text-2xl">{morph.lemma_text}</span>
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

      {segments.length > 0 && (
        <ul className="space-y-1 rounded-md bg-muted/50 p-2">
          {segments.map((s, i) => (
            <li key={i} className="flex justify-between gap-4">
              <span className="font-quran text-base">{s.segment}</span>
              <span className="text-xs text-muted-foreground text-left">
                {s.translation}
              </span>
            </li>
          ))}
        </ul>
      )}

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-muted-foreground">{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
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
