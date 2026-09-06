import "server-only";
import { z } from "zod";

/**
 * Secrets and server-to-server config. The `server-only` import above
 * makes accidentally importing this file from a Client Component a
 * BUILD ERROR, not just a documented rule someone has to remember —
 * see R&D doc Section 11 (never expose auth secrets to the browser).
 */
const serverEnvSchema = z.object({
  // Signs/verifies the session JWT — see lib/auth/session.ts.
  SESSION_SECRET: z.string().min(32, "SESSION_SECRET must be at least 32 characters"),
  // Presented as X-Internal-Secret on every call to core-api's
  // /internal/* routes — must match core-api's own INTERNAL_SHARED_SECRET.
  INTERNAL_SHARED_SECRET: z.string().min(1),
  // Server-to-server URL for core-api. Deliberately separate from the
  // NEXT_PUBLIC_CORE_API_URL in env.ts — that one may end up being a
  // different (public-facing) URL than the one our own server uses to
  // reach core-api directly, once this is actually deployed.
  CORE_API_INTERNAL_URL: z.url().default("http://localhost:8000"),
});

export const serverEnv = serverEnvSchema.parse({
  SESSION_SECRET: process.env.SESSION_SECRET,
  INTERNAL_SHARED_SECRET: process.env.INTERNAL_SHARED_SECRET,
  CORE_API_INTERNAL_URL: process.env.CORE_API_INTERNAL_URL,
});
