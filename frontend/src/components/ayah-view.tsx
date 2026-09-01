"use client";

import { useState } from "react";
import Link from "next/link";
import type { AyahWithWords } from "@/lib/api";
import { MorphPopover } from "@/components/morph-tooltip";
import { Button } from "@/components/ui/button";
import { Copy, Share2, Link2, Check } from "lucide-react";

export function AyahView({ ayah }: { ayah: AyahWithWords }) {
  const [copied, setCopied] = useState(false);

  async function copyText() {
    const text = ayah.text_uthmani ?? "";
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  }

  async function share() {
    const url = `${window.location.origin}/surahs/${ayah.surah}#ayah-${ayah.ayah}`;
    const text = ayah.text_uthmani ?? "";
    if (navigator.share) {
      try {
        await navigator.share({ title: `${ayah.surah_name} : ${ayah.ayah}`, text, url });
        return;
      } catch {}
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  }

  function copyLink() {
    const url = `${window.location.origin}/surahs/${ayah.surah}#ayah-${ayah.ayah}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  const hasWords = ayah.words.length > 0;

  return (
    <article
      id={`ayah-${ayah.ayah}`}
      className="group rounded-xl border bg-card p-5 space-y-4 scroll-mt-20 transition-colors hover:border-foreground/20"
    >
      {/* شريط علوي موحد */}
      <div className="flex items-center justify-between gap-4 border-b pb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center justify-center size-7 rounded-full bg-primary text-primary-foreground text-xs tabular-nums font-bold">
            {ayah.ayah.toLocaleString("ar-EG")}
          </span>
          <span className="text-xs text-muted-foreground tabular-nums">
            {ayah.surah_name} : {ayah.ayah.toLocaleString("ar-EG")}
          </span>
          {ayah.page_number ? (
            <Link
              href={`/surahs/${ayah.surah}?page=${ayah.page_number}`}
              className="text-[10px] leading-none px-1.5 py-0.5 rounded border tabular-nums hover:bg-accent"
            >
              ص {ayah.page_number.toLocaleString("ar-EG")}
            </Link>
          ) : null}
          {ayah.juz ? <span className="text-[10px] text-muted-foreground tabular-nums">ج {ayah.juz.toLocaleString("ar-EG")}</span> : null}
          {ayah.hizb ? <span className="text-[10px] text-muted-foreground tabular-nums">ح {ayah.hizb.toLocaleString("ar-EG")}</span> : null}
        </div>
        <div className="flex items-center gap-0.5 opacity-60 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="icon" className="size-7" onClick={copyText} aria-label="نسخ نص الآية">
            {copied ? <Check className="size-3.5 text-green-600" /> : <Copy className="size-3.5" />}
          </Button>
          <Button variant="ghost" size="icon" className="size-7" onClick={copyLink} aria-label="نسخ رابط الآية">
            <Link2 className="size-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="size-7" onClick={share} aria-label="مشاركة الآية">
            <Share2 className="size-3.5" />
          </Button>
        </div>
      </div>

      {/* عرض موحد: الكلمات هي نص الآية نفسه — تفاعلية للتحليل
          يرث حجم الخط من الحاوية الأب (surah-view-client) عبر fontSize inline، لذا لا نضع text-2xl ثابت هنا */}
      {hasWords ? (
        <div className="font-quran leading-[2.4] text-justify" dir="rtl" style={{ wordSpacing: "0.05em" }}>
          <div className="flex flex-wrap gap-x-1.5 gap-y-1 items-baseline">
            {ayah.words.map((entry) => (
              <MorphPopover key={entry.word_ayah_id} entry={entry} wordId={entry.word.id} />
            ))}
            <span className="inline-flex items-center justify-center ms-2 size-7 rounded-full border bg-muted/40 text-[11px] tabular-nums font-medium shrink-0 translate-y-0.5">
              ۝{ayah.ayah.toLocaleString("ar-EG")}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground/60 mt-3 text-center font-sans">اضغط على أي كلمة لعرض التحليل الصرفي</p>
        </div>
      ) : (
        ayah.text_uthmani && (
          <p className="font-quran leading-loose text-justify" dir="rtl">
            {ayah.text_uthmani}
            <span className="inline-flex items-center justify-center mx-2 size-7 rounded-full border bg-muted/40 text-xs tabular-nums">
              ۝{ayah.ayah.toLocaleString("ar-EG")}
            </span>
          </p>
        )
      )}
    </article>
  );
}
