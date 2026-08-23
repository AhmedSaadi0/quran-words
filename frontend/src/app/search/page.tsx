import type { Metadata } from "next";
import Link from "next/link";

import type { Word, Ayah, Derivative, Masdar } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SearchBar } from "@/components/search-bar";
import { RootCard } from "@/components/root-card";
import { api } from "@/lib/api";

interface SearchPageProps {
  searchParams: Promise<{ q?: string; type?: string }>;
}

export async function generateMetadata({
  searchParams,
}: SearchPageProps): Promise<Metadata> {
  const { q } = await searchParams;
  return { title: q ? `بحث: ${q}` : "بحث" };
}

function SectionTitle({
  title,
  count,
}: {
  title: string;
  count?: number;
}) {
  if (!count) return null;
  return (
    <h2 className="text-lg font-semibold">
      {title}{" "}
      <span className="text-sm font-normal text-muted-foreground tabular-nums">
        ({count.toLocaleString("ar-EG")})
      </span>
    </h2>
  );
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q = "" } = await searchParams;
  const query = q.trim();

  if (query.length < 2) {
    return (
      <div className="space-y-6 py-12 text-center">
        <h1 className="font-quran text-3xl">ابحث في كلمات القرآن</h1>
        <p className="text-muted-foreground">
          أدخل حرفين على الأقل — تجاهُل التشكيل مُطبَّق تلقائياً.
        </p>
        <div className="max-w-xl mx-auto">
          <SearchBar initialQuery={query} />
        </div>
      </div>
    );
  }

  const result = await api
    .search(query)
    .catch(() => null);

  if (!result) {
    return (
      <div className="space-y-6 py-12 text-center">
        <h1 className="font-quran text-3xl">تعذر الوصول إلى الخادم</h1>
        <p className="text-muted-foreground">
          تأكد من تشغيل الباكند على <code dir="ltr">localhost:8000</code> ثم أعد
          المحاولة.
        </p>
        <div className="max-w-xl mx-auto">
          <SearchBar initialQuery={query} />
        </div>
      </div>
    );
  }

  const empty =
    !result.roots.length &&
    !result.masadir.length &&
    !result.derivatives.length &&
    !result.words.length &&
    !result.ayat.length;

  if (empty) {
    return (
      <div className="space-y-6 py-12 text-center">
        <h1 className="font-quran text-3xl">لا نتائج لـ «{query}»</h1>
        <p className="text-muted-foreground">جرّب جذرًا ثلاثيًا مثل: كتب، علم، رحم.</p>
        <div className="max-w-xl mx-auto">
          <SearchBar initialQuery={query} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      <div className="space-y-4">
        <SearchBar compact={false} initialQuery={query} />
        <p className="text-xs text-muted-foreground">
          البحث المُطبَّع: «{result.normalized}»
        </p>
      </div>

      {result.roots.length > 0 && (
        <section className="space-y-3">
          <SectionTitle title="جذور" count={result.roots.length} />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {result.roots.map((r) => (
              <RootCard key={r.id} root={r} />
            ))}
          </div>
        </section>
      )}

      {result.masadir.length > 0 && (
        <section className="space-y-3">
          <SectionTitle title="مصادر" count={result.masadir.length} />
          <MasdarResults masadir={result.masadir} />
        </section>
      )}

      {result.derivatives.length > 0 && (
        <section className="space-y-3">
          <SectionTitle title="مشتقات" count={result.derivatives.length} />
          <DerivativeResults derivatives={result.derivatives} />
        </section>
      )}

      {result.words.length > 0 && (
        <section className="space-y-3">
          <SectionTitle title="كلمات" count={result.words.length} />
          <WordResults words={result.words} />
        </section>
      )}

      {result.ayat.length > 0 && (
        <section className="space-y-3">
          <SectionTitle title="آيات" count={result.ayat.length} />
          <AyahResults ayat={result.ayat} />
        </section>
      )}
    </div>
  );
}

function MasdarResults({ masadir }: { masadir: Masdar[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {masadir.map((m) => (
        <Link key={m.id} href={`/roots/${encodeURIComponent(m.root_text)}`}>
          <Card className="py-3 hover:bg-accent/40 transition-colors">
            <CardContent className="px-4 flex items-center gap-2">
              <span className="font-quran text-lg">{m.masdar_ar}</span>
              {m.is_attested && <Badge variant="gold">موثّق</Badge>}
              <span className="ms-auto text-xs text-muted-foreground">
                جذر: {m.root_text}
              </span>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function DerivativeResults({ derivatives }: { derivatives: Derivative[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {derivatives.map((d) => (
        <Link
          key={d.id}
          href={d.example_word ? `/words/${d.example_word}` : `/roots/${encodeURIComponent(d.root_text)}`}
        >
          <Card className="py-3 hover:bg-accent/40 transition-colors">
            <CardContent className="px-4 space-y-1">
              <p className="font-quran text-lg">
                {d.form_ar}
                {d.is_quranic && (
                  <Badge variant="gold" className="ms-2 align-middle">
                    قرآني
                  </Badge>
                )}
              </p>
              <p className="text-xs text-muted-foreground">{d.derivative_type}</p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function WordResults({ words }: { words: Word[] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {words.map((w) => (
        <Link key={w.id} href={`/words/${w.id}`}>
          <Card className="py-3 hover:bg-accent/40 transition-colors">
            <CardContent className="px-4 flex items-baseline justify-between gap-3">
              <span className="font-quran text-xl">{w.text}</span>
              <span className="text-xs text-muted-foreground truncate max-w-[50%]">
                {w.translation}
              </span>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}

function AyahResults({ ayat }: { ayat: Ayah[] }) {
  return (
    <ul className="space-y-2">
      {ayat.map((a) => (
        <li key={a.id}>
          <Link
            href={`/surahs/${a.surah}#ayah-${a.ayah}`}
            className="block rounded-lg border p-4 hover:bg-accent/40 transition-colors"
          >
            <p className="font-quran text-xl leading-relaxed">{a.text_uthmani}</p>
            <CardHeader className="px-0 pt-2 pb-0">
              <CardTitle className="text-xs font-normal text-muted-foreground">
                {a.surah_name} : {a.ayah}
              </CardTitle>
            </CardHeader>
          </Link>
        </li>
      ))}
    </ul>
  );
}
