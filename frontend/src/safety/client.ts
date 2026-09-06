import type { SafetyCheckRequest, SafetyCheckResult } from "./types";

/**
 * Calls the safety-service. Every caller MUST await this before sending
 * text to any LLM-backed feature or persisting/displaying it publicly.
 *
 * Not implemented yet — real wiring lands in Phase 5, once the
 * safety-service backend exists and has been reviewed. Until then this
 * throws loudly on purpose: a silent no-op stub here would be worse than
 * an obvious build-time error, because a future feature module could
 * accidentally ship "working" against a stub that never actually checks
 * anything.
 */
export async function checkText(
  _request: SafetyCheckRequest
): Promise<SafetyCheckResult> {
  throw new Error(
    "safety/client.ts: checkText() is not implemented yet. " +
      "This is expected in Phase 0. Do not build Phase 6 (AI Navigator) " +
      "against this stub — wire it for real in Phase 5 first."
  );
}
