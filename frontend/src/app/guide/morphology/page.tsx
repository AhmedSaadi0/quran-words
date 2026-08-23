import type { Metadata } from "next";
import Link from "next/link";

import { FIELDS, TERMS, type FieldKey } from "@/lib/morphology";

export const metadata: Metadata = {
  title: "دليل المصطلحات الصرفية",
  description:
    "شرح مبسط لكل رموز التحليل الصرفي في الموقع: نوع الكلمة، الباب، الزمن، البناء، الجنس والعدد، الاشتقاق.",
};

const FIELD_ORDER = Object.keys(FIELDS) as FieldKey[];

export default function MorphologyGuidePage() {
  return (
    <div className="space-y-8">
      <header className="space-y-2 border-b pb-6">
        <h1 className="text-3xl font-bold">دليل المصطلحات الصرفية</h1>
        <p className="text-muted-foreground leading-relaxed max-w-2xl">
          كل رمز يراه بجوار الكلمات في الموقع (مثل V أو IV أو PERF) له شرح هنا.
          اضغط أي مصطلح لقراءة تفصيله مع مثاله القرآني.
        </p>
      </header>

      {FIELD_ORDER.map((field) => {
        const terms = TERMS.filter((t) => t.field === field);
        if (!terms.length) return null;
        return (
          <section key={field} className="space-y-3">
            <div>
              <h2 className="text-xl font-semibold">{FIELDS[field].title}</h2>
              <p className="text-sm text-muted-foreground">{FIELDS[field].intro}</p>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {terms.map((t) => (
                <Link
                  key={t.key}
                  href={`/guide/morphology/${t.key}`}
                  className="rounded-lg border px-4 py-3 hover:bg-accent/40 transition-colors"
                >
                  <p className="font-semibold">{t.label}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground line-clamp-1">
                    {t.short}
                  </p>
                  <p dir="ltr" className="mt-1 text-[10px] text-muted-foreground/60 text-left font-mono">
                    {t.value}
                  </p>
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
