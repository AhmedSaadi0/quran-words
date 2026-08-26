"use client";

import Link from "next/link";
import { BookOpenText, Search, X } from "lucide-react";
import { useState } from "react";

import { SearchBar } from "@/components/search-bar";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";

export function SiteHeader({ showSearch = true }: { showSearch?: boolean }) {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-40">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-4 px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold shrink-0">
          <BookOpenText className="size-5" aria-hidden />
          <span>كلمات القرآن</span>
        </Link>

        {showSearch && (
          <div className="hidden sm:block flex-1 max-w-md">
            <SearchBar compact />
          </div>
        )}

        <nav className="ms-auto flex items-center gap-4 text-sm text-muted-foreground">
          <Link href="/surahs/1" className="hover:text-foreground transition-colors">
            السور
          </Link>
          <Link href="/guide/morphology" className="hover:text-foreground transition-colors">
            الدليل الصرفي
          </Link>
          <Link href="/sources" className="hover:text-foreground transition-colors">
            المصادر
          </Link>
        </nav>

        <ThemeToggle />

        {showSearch && (
          <Button
            variant="ghost"
            size="icon"
            className="sm:hidden shrink-0 -me-1"
            aria-label={isSearchOpen ? "إغلاق البحث" : "فتح البحث"}
            aria-expanded={isSearchOpen}
            onClick={() => setIsSearchOpen((v) => !v)}
          >
            {isSearchOpen ? <X className="size-5" /> : <Search className="size-5" />}
          </Button>
        )}
      </div>

      {showSearch && isSearchOpen && (
        <div className="border-t bg-background px-4 py-3 sm:hidden animate-in fade-in slide-in-from-top-1 duration-150">
          <SearchBar compact autoFocus onNavigate={() => setIsSearchOpen(false)} />
        </div>
      )}
    </header>
  );
}
