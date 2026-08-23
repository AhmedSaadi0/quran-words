import type { Metadata } from "next";

import { SearchBar } from "@/components/search-bar";
import { RootCard, StatsCards } from "@/components/root-card";
import { PaginationControls } from "@/components/pagination-controls";
import { api } from "@/lib/api";

export const metadata: Metadata = {
  title: "كلمات القرآن — جذور ومصادر ومشتقات",
};

interface HomePageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);

  const [stats, roots] = await Promise.all([
    api.stats(),
    api.roots({ page }),
  ]);

  return (
    <div className="space-y-10">
      <section className="space-y-6 pt-6 text-center">
        <h1 className="font-quran text-4xl font-bold">
          كلمات القرآن
        </h1>
        <p className="text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          تصفح الكلمات القرآنية الفريدة مع جذورها المدققة، ومصادرها، ومشتقاتها،
          والتحليل الصرفي لكل موضع.
        </p>
        <div className="max-w-2xl mx-auto">
          <SearchBar compact={false} />
        </div>
      </section>

      <StatsCards stats={stats} />

      <section id="roots" className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">الجذور</h2>
          <span className="text-sm text-muted-foreground tabular-nums">
            {roots.count.toLocaleString("ar-EG")} جذر
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {roots.results.map((r) => (
            <RootCard key={r.id} root={r} />
          ))}
        </div>

        <PaginationControls
          page={page}
          count={roots.count}
          pageSize={20}
          basePath="/"
        />
      </section>
    </div>
  );
}
