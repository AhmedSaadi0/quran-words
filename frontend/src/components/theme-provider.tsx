"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
// next-themes injects a <script> for theme detection (dangerouslySetInnerHTML).
// React 19 warns "Encountered a script tag while rendering React component" in dev
// even though the script is never executed on client — benign, upstream issue.

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
