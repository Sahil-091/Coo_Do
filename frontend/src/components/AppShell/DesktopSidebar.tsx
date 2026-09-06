"use client";

import { SafetyDisclosure } from "@/components/SafetyDisclosure";
import { cn } from "@/lib/cn";
import { PRIMARY_NAV_ITEMS, SECONDARY_NAV_ITEMS, type NavItem } from "@/lib/nav-config";
import { useIsActivePath } from "@/lib/use-is-active-path";
import Link from "next/link";

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
    <aside className="hidden w-64 shrink-0 flex-col border-r border-border-subtle bg-paper-raised px-4 py-6 md:flex">
      <Link href="/" className="font-display px-3 pb-6 text-xl text-ink">
        Campus Connect
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

      <div className="mt-auto pt-4">
        <SafetyDisclosure />
      </div>
    </aside>
  );
}
