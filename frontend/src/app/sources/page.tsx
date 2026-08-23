import type { Metadata } from "next";

import { api } from "@/lib/api";

export const metadata: Metadata = {
  title: "المصادر والتراخيص",
};

export default async function SourcesPage() {
  let sources: Awaited<ReturnType<typeof api.sources>> = [];
  try {
    sources = await api.sources();
  } catch {
    // backend unreachable — still render the license notice below
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-bold">المصادر والتراخيص</h1>
      <p className="text-muted-foreground leading-relaxed">
        تُبنى بيانات هذا الموقع على مصادر مفتوحة، نشكر أصحابها.
      </p>

      <ul className="space-y-4">
        {sources.map((s) => (
          <li key={s.id} className="rounded-xl border p-4 space-y-1">
            <p className="font-semibold">{s.name}</p>
            {s.description && (
              <p className="text-sm text-muted-foreground">{s.description}</p>
            )}
            {s.url && (
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                dir="ltr"
                className="text-xs underline underline-offset-2 text-muted-foreground hover:text-foreground"
              >
                {s.url}
              </a>
            )}
          </li>
        ))}
      </ul>

      <section className="rounded-xl border p-4 text-sm leading-relaxed space-y-2">
        <p className="font-semibold">ملاحظة الترخيص (GPL)</p>
        <p className="text-muted-foreground">
          بيانات Quranic Arabic Corpus مرخّصة تحت رخصة GNU General Public License،
          وهذا المشروع يوفر كوده المصدري علناً وفقاً لشروط الرخصة.
        </p>
      </section>
    </div>
  );
}
