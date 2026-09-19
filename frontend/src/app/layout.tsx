import type { Metadata, Viewport } from "next";
import { RegisterServiceWorker } from "@/components/RegisterServiceWorker";
import "./globals.css";

// Deliberately using the system font stack (see globals.css) rather than
// next/font/google for this scaffold: fetching Google Fonts at build time
// requires open egress to fonts.googleapis.com, which not every CI/deploy
// environment has (this sandbox doesn't either — that's how this got
// caught). Phase 1 (design system) is where typography should be a
// deliberate choice; if a webfont is wanted then, prefer next/font/local
// with self-hosted files or an npm-distributed font package so the build
// doesn't depend on runtime access to an external font CDN.

export const metadata: Metadata = {
  title: "Coo_Do",
  description:
    "Small, real-world actions toward connection and wellbeing.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Coo_Do",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#6841d8",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        {children}
        <RegisterServiceWorker />
      </body>
    </html>
  );
}
