"use client";

import { MoreHorizontal } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AdaptivePanel } from "@/components/ui/AdaptivePanel";
import { SafetyDisclosure } from "@/components/SafetyDisclosure";
import { cn } from "@/lib/cn";
import { PRIMARY_NAV_ITEMS, SECONDARY_NAV_ITEMS } from "@/lib/nav-config";
import { isPathActive, useIsActivePath } from "@/lib/use-is-active-path";

function TabLink({ href, label, icon: Icon }: (typeof PRIMARY_NAV_ITEMS)[number]) {
  const active = useIsActivePath(href);
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className="flex flex-1 flex-col items-center gap-1 rounded-md px-1 py-1.5 text-[11px] text-ink-muted transition-colors hover:text-ink"
    >
      <span
        className={cn(
          "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
          active && "bg-lamp-tint"
        )}
      >
        <Icon
          className={cn("h-5 w-5", active ? "text-lamp" : "text-current")}
          aria-hidden="true"
        />
      </span>
      <span className={cn(active && "font-medium text-ink")}>{label}</span>
    </Link>
  );
}

export function MobileTabBar() {
  const [moreOpen, setMoreOpen] = useState(false);
  const pathname = usePathname();
  const secondaryActive = SECONDARY_NAV_ITEMS.some((item) => isPathActive(pathname, item.href));

  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 flex flex-col gap-2 border-t border-border-subtle bg-paper px-3 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-2 md:hidden"
    >
      <SafetyDisclosure />
      <div className="flex items-stretch">
        {PRIMARY_NAV_ITEMS.map((item) => (
          <TabLink key={item.href} {...item} />
        ))}
        <button
          type="button"
          onClick={() => setMoreOpen(true)}
          aria-haspopup="dialog"
          aria-expanded={moreOpen}
          className="flex flex-1 flex-col items-center gap-1 rounded-md px-1 py-1.5 text-[11px] text-ink-muted transition-colors hover:text-ink"
        >
          <span
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full transition-colors",
              secondaryActive && "bg-lamp-tint"
            )}
          >
            <MoreHorizontal
              className={cn("h-5 w-5", secondaryActive ? "text-lamp" : "text-current")}
              aria-hidden="true"
            />
          </span>
          <span className={cn(secondaryActive && "font-medium text-ink")}>More</span>
        </button>
      </div>

      <AdaptivePanel open={moreOpen} onClose={() => setMoreOpen(false)} title="More">
        <ul className="flex flex-col gap-1">
          {SECONDARY_NAV_ITEMS.map(({ href, label, icon: Icon, description }) => (
            <li key={href}>
              <Link
                href={href}
                onClick={() => setMoreOpen(false)}
                className="flex items-center gap-3 rounded-md px-3 py-3 text-sm text-ink hover:bg-paper"
              >
                <Icon className="h-5 w-5 text-ink-muted" aria-hidden="true" />
                <span className="flex flex-col">
                  <span className="font-medium">{label}</span>
                  <span className="text-xs text-ink-muted">{description}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </AdaptivePanel>
    </nav>
  );
}
