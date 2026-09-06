import { DesktopSidebar } from "./DesktopSidebar";
import { MobileTabBar } from "./MobileTabBar";
import { SkipLink } from "@/components/SkipLink";

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
        {/* Slim mobile header — desktop already shows the wordmark in the sidebar. */}
        <header className="flex items-center border-b border-border-subtle px-4 py-3 md:hidden">
          <span className="font-display text-lg text-ink">Campus Connect</span>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 px-4 pb-36 pt-4 outline-none md:px-8 md:pb-8 md:pt-8"
        >
          {children}
        </main>
      </div>

      <MobileTabBar />
    </div>
  );
}
