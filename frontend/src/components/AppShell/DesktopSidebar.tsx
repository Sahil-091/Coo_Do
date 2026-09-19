"use client";

import { cn } from "@/lib/cn";
import { PRIMARY_NAV_ITEMS, SECONDARY_NAV_ITEMS, type NavItem } from "@/lib/nav-config";
import { useIsActivePath } from "@/lib/use-is-active-path";
import Link from "next/link";
import { HeartHandshake, Moon, UsersRound } from "lucide-react";

function SidebarLink({ href, label, icon: Icon }: NavItem) {
  const active = useIsActivePath(href);
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
        active ? "bg-lamp-tint font-medium text-ink" : "text-ink-muted hover:bg-paper hover:text-ink"
      )}
    >
      <Icon className={cn("h-5 w-5", active ? "text-lamp" : "text-current")} aria-hidden="true" />
      {label}
    </Link>
  );
}

export function DesktopSidebar() {
  return (
    <aside className="hidden w-[17rem] shrink-0 flex-col border-r border-border-subtle bg-paper-raised px-5 py-5 md:flex">
      <Link href="/" className="flex items-center gap-2 px-2 pb-9">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-lamp-tint text-lamp"><UsersRound className="h-6 w-6" aria-hidden="true" /></span>
        <span><span className="block text-xl font-bold tracking-tight text-ink">Coo_<span className="text-lamp">Do</span></span><span className="block text-[11px] text-ink-muted">You&apos;re not alone here</span></span>
      </Link>

      <nav aria-label="Primary" className="flex flex-col gap-1">
        {PRIMARY_NAV_ITEMS.map((item) => (
          <SidebarLink key={item.href} {...item} />
        ))}
      </nav>

      <div className="my-4 border-t border-border-subtle" />

      <nav aria-label="More" className="flex flex-col gap-1">
        {SECONDARY_NAV_ITEMS.map((item) => (
          <SidebarLink key={item.href} {...item} />
        ))}
      </nav>

      <div className="mt-auto space-y-4 pt-5">
        <div className="rounded-xl border border-[#f7dfe2] bg-clay-tint p-4"><HeartHandshake className="mb-2 h-6 w-6 text-clay" aria-hidden="true" /><p className="text-sm font-bold text-clay">Need immediate help?</p><p className="mt-1 text-xs leading-5 text-ink-muted">You matter. Reach out.</p><Link href="/safety" className="mt-3 flex items-center justify-center rounded-md bg-clay px-3 py-2 text-xs font-semibold text-white hover:bg-clay/90">View safety plan</Link></div>
        <div className="flex items-center gap-2 px-2 text-sm text-ink-muted"><Moon className="h-4 w-4" aria-hidden="true" />Dark mode<span className="ml-auto h-5 w-9 rounded-full bg-[#dedbe5] p-0.5"><span className="block h-4 w-4 rounded-full bg-white shadow-sm" /></span></div>
      </div>
    </aside>
  );
}
