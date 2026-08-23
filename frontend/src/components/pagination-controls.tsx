import Link from "next/link";

import { Button } from "@/components/ui/button";

export function PaginationControls({
  page,
  count,
  pageSize,
  basePath,
  extraParams = {},
}: {
  page: number;
  count: number;
  pageSize: number;
  basePath: string;
  extraParams?: Record<string, string>;
}) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (totalPages <= 1) return null;

  function hrefFor(p: number) {
    const params = new URLSearchParams(extraParams);
    params.set("page", String(p));
    return `${basePath}?${params.toString()}`;
  }

  return (
    <nav className="flex items-center justify-center gap-3" aria-label="ترقيم الصفحات">
      {page > 1 ? (
        <Button variant="outline" size="sm" asChild>
          <Link href={hrefFor(page - 1)}>السابق</Link>
        </Button>
      ) : (
        <Button variant="outline" size="sm" disabled>
          السابق
        </Button>
      )}

      <span className="text-sm text-muted-foreground tabular-nums">
        صفحة {page.toLocaleString("ar-EG")} من {totalPages.toLocaleString("ar-EG")}
      </span>

      {page < totalPages ? (
        <Button variant="outline" size="sm" asChild>
          <Link href={hrefFor(page + 1)}>التالي</Link>
        </Button>
      ) : (
        <Button variant="outline" size="sm" disabled>
          التالي
        </Button>
      )}
    </nav>
  );
}
