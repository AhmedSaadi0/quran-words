import Link from "next/link";

import { getTerm, type FieldKey } from "@/lib/morphology";

/**
 * يعرض قيمة صرفية كرابط منقّط لدليلها إن وُجد شرحها،
 * وإلا يظهرها نصاً خاماً.
 */
export function TermValue({
  field,
  value,
  className = "",
}: {
  field: FieldKey;
  value?: string | null;
  className?: string;
}) {
  if (!value) return null;
  const term = getTerm(field, value);
  if (!term) return <span className={className}>{value}</span>;
  return (
    <Link
      href={`/guide/morphology/${term.key}`}
      title={term.short}
      className={`underline decoration-dotted underline-offset-4 hover:text-foreground ${className}`}
    >
      {term.label}
    </Link>
  );
}
