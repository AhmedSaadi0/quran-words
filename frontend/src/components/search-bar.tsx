"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface SearchBarProps {
  compact?: boolean;
  initialQuery?: string;
}

export function SearchBar({ compact = false, initialQuery = "" }: SearchBarProps) {
  const router = useRouter();
  const [value, setValue] = useState(initialQuery);
  const [pending, setPending] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSubmitted = useRef<string>(initialQuery);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setValue(q);
    if (timerRef.current) clearTimeout(timerRef.current);

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
      setPending(false);
    }, 300);
  }

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        const q = value.trim();
        if (q.length >= 2) router.push(`/search?q=${encodeURIComponent(q)}`);
      }}
      className={cn("relative", compact ? "w-full" : "w-full")}
    >
      <Search className="absolute end-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
      <Input
        type="search"
        value={value}
        onChange={onChange}
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
