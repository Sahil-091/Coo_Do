import type { TimeOfDay } from "./types";

/**
 * Deliberately computed from the STUDENT's local time (call this
 * client-side, at submission time) — never the server's clock, which
 * could be in a different timezone entirely. This directly feeds the
 * "lonely at night" modifier in the backend's routing rules, so getting
 * "night" to actually mean night for this specific student matters.
 */
export function getTimeOfDay(date: Date): TimeOfDay {
  const hour = date.getHours();
  if (hour >= 5 && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 21) return "evening";
  return "night";
}
