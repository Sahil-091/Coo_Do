import { NextResponse, type NextRequest } from "next/server";
import { getSessionPayload } from "@/lib/auth/session";

/**
 * Deliberately inverted from the "list every protected route" pattern:
 * this is the small PUBLIC allowlist, and everything else requires a
 * session by default. Fail-secure as new routes get added — nobody has
 * to remember to add them to a protected-routes list.
 */
const PUBLIC_ROUTES = ["/login", "/sign-up"];

/**
 * Optimistic check only (R&D doc's own Next.js authentication guide is
 * explicit about this): reads the JWT from the cookie, does NOT hit the
 * database. The real, DB-authoritative gate — especially for the age
 * check — lives in lib/auth/dal.ts's requireOnboardedUser(), called
 * from (app)'s layout. This proxy exists to bounce obviously-
 * unauthenticated requests early, not as the actual security boundary.
 */
export async function proxy(req: NextRequest) {
  const path = req.nextUrl.pathname;
  const isPublicRoute = PUBLIC_ROUTES.includes(path);

  const session = await getSessionPayload();
  const isAuthenticated = Boolean(session?.userId);

  if (!isPublicRoute && !isAuthenticated) {
    return NextResponse.redirect(new URL("/login", req.nextUrl));
  }

  if (isPublicRoute && isAuthenticated) {
    return NextResponse.redirect(new URL("/", req.nextUrl));
  }

  return NextResponse.next();
}

export const config = {
  // Exclude: Next.js internals, the PWA shell assets (must work whether
  // or not the visitor is logged in — installability shouldn't require
  // auth), and the offline fallback page (an SW fallback, not a real
  // navigable screen).
  matcher: [
    "/((?!api|_next/static|_next/image|sw\\.js|manifest\\.webmanifest|icons/|offline|favicon\\.ico|icon\\.png|apple-icon\\.png).*)",
  ],
};
