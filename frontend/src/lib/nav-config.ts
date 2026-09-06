import {
  BookOpen,
  Footprints,
  Home,
  LifeBuoy,
  Settings,
  Shield,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  group: "primary" | "secondary";
  /** Used for aria-label context, not shown visually in the shell. */
  description: string;
}

/**
 * Single source of truth for navigation. The mobile tab bar renders
 * `primary` items plus a "More" trigger for `secondary`; the desktop
 * sidebar renders both groups directly (divided). Both consume this
 * same array — see AppShell's README for why that split exists.
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", icon: Home, group: "primary", description: "Your home screen" },
  {
    href: "/checkin",
    label: "Check-in",
    icon: Sparkles,
    group: "primary",
    description: "A 60-second check-in",
  },
  {
    href: "/tiny-action",
    label: "Tiny Action",
    icon: Footprints,
    group: "primary",
    description: "One small, achievable step",
  },
  {
    href: "/community",
    label: "Community",
    icon: Users,
    group: "primary",
    description: "Situation rooms and shared activities",
  },
  {
    href: "/journal",
    label: "Journal",
    icon: BookOpen,
    group: "primary",
    description: "Your private reflections over time",
  },
  {
    href: "/professional-help",
    label: "Professional help",
    icon: LifeBuoy,
    group: "secondary",
    description: "Find and prepare for real-world support",
  },
  {
    href: "/safety",
    label: "Safety Center",
    icon: Shield,
    group: "secondary",
    description: "Crisis resources and safety tools",
  },
  {
    href: "/settings",
    label: "Settings",
    icon: Settings,
    group: "secondary",
    description: "Account and privacy settings",
  },
];

export const PRIMARY_NAV_ITEMS = NAV_ITEMS.filter((item) => item.group === "primary");
export const SECONDARY_NAV_ITEMS = NAV_ITEMS.filter((item) => item.group === "secondary");
