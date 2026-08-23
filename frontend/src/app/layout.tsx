import type { Metadata } from "next";
import "./globals.css";

import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: {
    default: "كلمات القرآن — جذور ومصادر ومشتقات",
    template: "%s | كلمات القرآن",
  },
  description:
    "تصفح 21,295 كلمة قرآنية فريدة مع جذورها المدققة ومصادرها ومشتقاتها وتحليلها الصرفي.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ar" dir="rtl" className="h-full antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col">
        <SiteHeader />
        <main className="flex-1 mx-auto w-full max-w-5xl px-4 py-8">{children}</main>
        <footer className="border-t py-6">
          <p className="mx-auto max-w-5xl px-4 text-xs text-muted-foreground">
            البيانات من Quranic Arabic Corpus (GPL) و Quran.com API و CAMeL Tools —
            انظر صفحة المصادر.
          </p>
        </footer>
      </body>
    </html>
  );
}
