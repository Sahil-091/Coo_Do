/**
 * Typed, validated environment access. Import from here instead of
 * reading `process.env.X` directly elsewhere, so a missing/malformed
 * var fails loudly at startup rather than as an undefined deep in a
 * feature module.
 */
import { z } from "zod";

const clientEnvSchema = z.object({
  NEXT_PUBLIC_CORE_API_URL: z.url().default("http://localhost:8000"),
  NEXT_PUBLIC_SAFETY_SERVICE_URL: z.url().default("http://localhost:8001"),
});

export const env = clientEnvSchema.parse({
  NEXT_PUBLIC_CORE_API_URL: process.env.NEXT_PUBLIC_CORE_API_URL,
  NEXT_PUBLIC_SAFETY_SERVICE_URL: process.env.NEXT_PUBLIC_SAFETY_SERVICE_URL,
});
