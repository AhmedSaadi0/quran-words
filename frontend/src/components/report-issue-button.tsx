"use client";

import { useEffect, useState } from "react";
import { Flag, ExternalLink } from "lucide-react";

import { Button } from "@/components/ui/button";
import { buildGithubIssueUrl } from "@/lib/github";

interface ReportIssueButtonProps {
  rootText: string;
  rootId?: number | null;
  /** Optional override for the page URL; defaults to window.location.href */
  pageUrl?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
}

export function ReportIssueButton({
  rootText,
  rootId,
  pageUrl,
  variant = "outline",
  size = "sm",
  className,
}: ReportIssueButtonProps) {
  const [href, setHref] = useState(() =>
    buildGithubIssueUrl({ rootText, rootId, pageUrl: pageUrl ?? null })
  );

  // Sync href with actual page URL after mount to avoid hydration mismatch (SSR has no window)
  useEffect(() => {
    const actualUrl = pageUrl ?? (typeof window !== "undefined" ? window.location.href : null);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional sync after mount
    setHref(buildGithubIssueUrl({ rootText, rootId, pageUrl: actualUrl }));
  }, [rootText, rootId, pageUrl]);

  return (
    <Button
      asChild
      variant={variant}
      size={size}
      className={className}
    >
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`الإبلاغ عن معنى للجذر ${rootText} عبر GitHub`}
      >
        <Flag className="size-4" aria-hidden />
        <span>الإبلاغ عن معنى</span>
        <ExternalLink className="size-3 opacity-60" aria-hidden />
      </a>
    </Button>
  );
}

interface ReportIssueCardProps {
  rootText: string;
  rootId?: number | null;
}

export function ReportIssueCard({ rootText, rootId }: ReportIssueCardProps) {
  return (
    <div
      dir="rtl"
      className="rounded-xl border border-dashed bg-amber-50/60 px-4 py-4 dark:bg-amber-950/20 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="space-y-1 text-right">
        <p className="text-sm font-medium leading-none">
          هل وجدت معنى غير صحيح أو ناقص؟
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          ساهم في تحسين البيانات — سيُفتح نموذج بلاغ جاهز على GitHub.
          <span dir="ltr" className="mx-1 hidden sm:inline text-muted-foreground/70">
            / Found an issue? Report on GitHub.
          </span>
        </p>
      </div>
      <ReportIssueButton
        rootText={rootText}
        rootId={rootId}
        className="shrink-0 self-start sm:self-auto"
      />
    </div>
  );
}
