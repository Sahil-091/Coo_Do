import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { internalApiFetch } from "@/lib/core-api-server";
import { getSessionPayload } from "./session";

export interface CurrentUser {
  userId: string;
  email: string;
  ageVerified: boolean;
  pseudonymousDisplayName: string | null;
}

interface UserStateResponse {
  user_id: string;
  email: string;
  age_verified: boolean;
  pseudonymous_display_name: string | null;
}

/**
 * Confirms the session JWT itself is valid. This is the "optimistic"
 * half — it does NOT hit the database, matching proxy.ts's own check.
 * Memoized per request so multiple call sites don't re-verify the JWT
 * repeatedly during one render pass.
 */
export const verifySession = cache(async (): Promise<{ userId: string } | null> => {
  const payload = await getSessionPayload();
  if (!payload?.userId) return null;
  return { userId: payload.userId };
});

/**
 * The "secure" half — fresh, DB-authoritative user state via core-api.
 * Deliberately NOT cached in the JWT itself (see session.ts's payload
 * comment): age_verified in particular must never be read from a
 * possibly-stale token, since the whole point of the age gate is that
 * it's authoritative. Memoized via React's cache() so this only hits
 * core-api once per request, however many components ask for it.
 */
export const getCurrentUser = cache(async (): Promise<CurrentUser | null> => {
  const session = await verifySession();
  if (!session) return null;

  try {
    const user = await internalApiFetch<UserStateResponse>(`/internal/users/${session.userId}`);
    return {
      userId: user.user_id,
      email: user.email,
      ageVerified: user.age_verified,
      pseudonymousDisplayName: user.pseudonymous_display_name,
    };
  } catch {
    // core-api unreachable, or this user_id no longer exists (e.g. a
    // deleted account) — fail closed as "not authenticated", never
    // crash the page over it.
    return null;
  }
});

/** For (onboarding) sub-pages: needs a real signed-in user, but NOT full onboarding yet. */
export async function requireAuthenticatedUser(): Promise<CurrentUser> {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}

/**
 * For (app) routes — the actual hard gate (R&D doc Section 11/17:
 * "Age handling is a hard gate, not a soft field"). This is what makes
 * it a real gate rather than a UI suggestion: every (app) page runs
 * this, server-side, against fresh data, before rendering anything.
 */
export async function requireOnboardedUser(): Promise<CurrentUser> {
  const user = await requireAuthenticatedUser();
  if (!user.ageVerified) redirect("/onboarding/age");
  return user;
}
