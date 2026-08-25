import Link from "next/link";

import type { AyahWithWords } from "@/lib/api";

export function RootAyahList({
  ayat,
  rootText,
}: {
  ayat: AyahWithWords[];
  rootText: string;
}) {
  if (!ayat.length) {
    return <p className="text-sm text-muted-foreground">لا توجد آيات لهذا الجذر.</p>;
  }

  return (
    <div className="space-y-3" dir="rtl">
      <p className="text-xs text-muted-foreground tabular-nums">
        {ayat.length.toLocaleString("ar-EG")} آية مرتبة حسب المصحف — الكلمات المميزة هي مشتقات الجذر{" "}
        <span className="font-quran text-sm">{rootText}</span>
      </p>
      <ul className="divide-y rounded-xl border overflow-hidden">
        {ayat.map((ayah) => {
          // حدد الكلمات التي تطابق الجذر مباشرة
          const matchedPositions = new Set(
            ayah.words
              .filter((w) => w.morphology?.root_text === rootText)
              .map((w) => w.position)
          );
          const hasMatches = matchedPositions.size > 0;

          return (
            <li key={ayah.id} className="px-4 py-4 space-y-2.5 text-right" dir="rtl">
              <div className="flex items-center justify-between gap-3">
                <Link
                  href={`/surahs/${ayah.surah}#ayah-${ayah.ayah}`}
                  className="text-xs text-muted-foreground hover:text-foreground tabular-nums underline-offset-2 hover:underline"
                >
                  {ayah.surah_name} : {ayah.ayah}
                </Link>
                {hasMatches && (
                  <span className="text-[11px] text-muted-foreground">
                    {matchedPositions.size.toLocaleString("ar-EG")} كلمة من الجذر
                  </span>
                )}
              </div>

              {/* نص الآية مع تمييز الكلمات */}
              <div
                className="font-quran text-2xl leading-loose text-right flex flex-wrap gap-x-1 gap-y-1 justify-start"
                dir="rtl"
              >
                {ayah.words.length ? (
                  ayah.words.map((entry) => {
                    const isMatch = entry.morphology?.root_text === rootText;
                    return (
                      <Link
                        key={entry.word_ayah_id}
                        href={`/words/${entry.word.id}`}
                        className={
                          isMatch
                            ? "rounded-md bg-amber-100 dark:bg-amber-900/40 px-1 py-0.5 hover:bg-amber-200 dark:hover:bg-amber-800/50 transition-colors"
                            : "hover:bg-accent/40 rounded-md px-0.5 transition-colors"
                        }
                        title={isMatch ? `جذر: ${rootText}` : undefined}
                      >
                        {entry.word.text}
                      </Link>
                    );
                  })
                ) : (
                  <span>{ayah.text_uthmani}</span>
                )}
              </div>

              {/* نص عثماني احتياطي إذا لم تتوفر الكلمات المفصلة */}
              {!ayah.words.length && ayah.text_uthmani && (
                <p className="font-quran text-xl leading-relaxed text-right">
                  ﴿{ayah.text_uthmani}﴾
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
