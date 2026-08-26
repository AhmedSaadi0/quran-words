"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  compact?: boolean;
  initialQuery?: string;
  autoFocus?: boolean;
  onNavigate?: () => void;
}

export function SearchBar({
  compact = false,
  initialQuery = "",
  autoFocus = false,
  onNavigate,
}: SearchBarProps) {
  const router = useRouter();
  const [value, setValue] = useState(initialQuery);
  const [pending, setPending] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSubmitted = useRef<string>(initialQuery);
  const isComposing = useRef(false);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setValue(q);
    if (timerRef.current) clearTimeout(timerRef.current);

    if (isComposing.current) return;

    if (q.trim().length < 2) {
      setPending(false);
      return;
    }
    setPending(true);
    timerRef.current = setTimeout(() => {
      const trimmed = q.trim();
      if (trimmed === lastSubmitted.current) {
        setPending(false);
        return;
      }
      lastSubmitted.current = trimmed;
      router.push(`/search?q=${encodeURIComponent(trimmed)}`);
      onNavigate?.();
      setPending(false);
    }, 300);
  }

  return (
    <form
      role="search"
      action="/search"
      method="get"
      onSubmit={(e) => {
        e.preventDefault();
        const q = value.trim();
        if (q.length >= 2) {
          // keep lastSubmitted in sync for submit path as well
          lastSubmitted.current = q;
          router.push(`/search?q=${encodeURIComponent(q)}`);
          onNavigate?.();
        }
      }}
      className={cn("relative", compact ? "w-full" : "w-full")}
    >
      <Search className="absolute end-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
      <Input
        type="search"
        name="q"
        value={value}
        onChange={onChange}
        onCompositionStart={() => {
          isComposing.current = true;
        }}
        onCompositionEnd={(e) => {
          isComposing.current = false;
          // trigger debounced search after composition ends (e.g. Arabic suggestions)
          onChange(e as unknown as React.ChangeEvent<HTMLInputElement>);
        }}
        autoFocus={autoFocus}
        enterKeyHint="search"
        inputMode="search"
        autoComplete="off"
        spellCheck={false}
        placeholder="ابحث بجذر: كتب / بمصدر: كتابة / بكلمة: عَلِيم"
        aria-label="بحث في كلمات القرآن"
        className={cn(
          "pe-9 bg-background",
          compact ? "h-9" : "h-12 rounded-xl text-lg pe-10 shadow-md"
        )}
      />
      {pending && (
        <Loader2 className="absolute start-3 top-1/2 -translate-y-1/2 size-4 animate-spin text-muted-foreground" />
      )}
    </form>
  );
}
