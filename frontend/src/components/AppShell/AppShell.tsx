import { DesktopSidebar } from "./DesktopSidebar";
import { MobileTabBar } from "./MobileTabBar";
import { SkipLink } from "@/components/SkipLink";
import { Bell, Menu, UserRound } from "lucide-react";
import { InstallPrompt } from "@/components/InstallPrompt";
import { NetworkStatus } from "@/components/NetworkStatus";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col md:flex-row">
      {/*
        DesktopSidebar and MobileTabBar both render a <nav aria-label="Primary">
        — that's intentional, not a duplicate-landmark bug. Only one is ever
        actually perceivable at a given viewport: each is CSS-toggled via
        `hidden`/`md:flex` or `md:hidden`, and `display:none` content is
        removed from the accessibility tree per spec, not just visually
        hidden. This is the standard pattern for a CSS-only responsive shell
        (no separate mobile/desktop codepaths) — don't "fix" it by adding
        JS-based conditional rendering instead.
      */}
      <SkipLink />
      <DesktopSidebar />

      <div className="flex flex-1 flex-col">
        <header className="flex h-[74px] items-center justify-between border-b border-border-subtle bg-white px-4 md:px-7">
          <div className="flex items-center gap-3"><Menu className="h-5 w-5 text-ink" aria-hidden="true" /><span className="font-display text-lg text-ink md:hidden">Coo_Do</span></div>
          <div className="flex items-center gap-4"><button aria-label="Notifications" className="rounded-full p-2 text-ink-muted hover:bg-lamp-tint hover:text-lamp"><Bell className="h-5 w-5" aria-hidden="true" /></button><div className="hidden items-center gap-2 border-l border-border-subtle pl-4 sm:flex"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-lamp-tint text-lamp"><UserRound className="h-5 w-5" aria-hidden="true" /></span><span className="text-sm font-semibold text-ink">Sahil Singh</span></div></div>
        </header>
        <NetworkStatus />
        <InstallPrompt />

        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 px-4 pb-36 pt-5 outline-none md:px-7 md:pb-8 md:pt-7"
        >
          {children}
        </main>
      </div>

      <MobileTabBar />
    </div>
  );
}
