"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mounted guard for hydration (next-themes pattern)
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="shrink-0"
        aria-label="تبديل الثيم"
        disabled
      >
        <Sun className="size-5" aria-hidden />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      className="shrink-0 relative"
      aria-label={isDark ? "تفعيل الوضع الفاتح" : "تفعيل الوضع المظلم"}
      title={isDark ? "تفعيل الوضع الفاتح" : "تفعيل الوضع المظلم"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <Sun
        className="size-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"
        aria-hidden
      />
      <Moon
        className="absolute size-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
        aria-hidden
      />
      <span className="sr-only">تبديل الثيم</span>
    </Button>
  );
}
