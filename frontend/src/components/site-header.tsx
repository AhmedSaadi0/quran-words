import Link from "next/link";
import { BookOpenText } from "lucide-react";

import { SearchBar } from "@/components/search-bar";

export function SiteHeader({ showSearch = true }: { showSearch?: boolean }) {
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
          <Link href="/sources" className="hover:text-foreground transition-colors">
            المصادر
          </Link>
        </nav>
      </div>
    </header>
  );
}
