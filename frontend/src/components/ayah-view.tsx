import type { AyahWithWords } from "@/lib/api";
import { MorphPopover } from "@/components/morph-tooltip";

export function AyahView({ ayah }: { ayah: AyahWithWords }) {
  return (
    <article
      id={`ayah-${ayah.ayah}`}
      className="rounded-xl border p-5 space-y-3"
    >
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-xs text-muted-foreground tabular-nums">
          {ayah.surah_name} : {ayah.ayah}
        </span>
        <span className="font-quran text-lg text-muted-foreground">
          ﴿{ayah.text_uthmani}﴾
        </span>
      </div>

      <div className="flex flex-wrap gap-x-1 gap-y-2" dir="rtl">
        {ayah.words.map((entry) => (
          <MorphPopover
            key={entry.word_ayah_id}
            entry={entry}
            wordId={entry.word.id}
          />
        ))}
      </div>
    </article>
  );
}
