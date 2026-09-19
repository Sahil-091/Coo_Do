"use client";

import { usePathname } from "next/navigation";

/** Pure comparison — safe to call inside .some()/.map(), no hook rules apply. */
export function isPathActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

/** Hook form for a single nav item's own active state. */
export function useIsActivePath(href: string) {
  const pathname = usePathname();
  return isPathActive(pathname, href);
}
