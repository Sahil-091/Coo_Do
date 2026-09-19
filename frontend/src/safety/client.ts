import type { SafetyCheckRequest, SafetyCheckResult } from "./types";

/**
 * Calls the safety-service. Every caller MUST await this before sending
 * text to any LLM-backed feature or persisting/displaying it publicly.
 *
 * This browser helper calls a same-origin route. The route resolves the
 * signed-in user server-side and authenticates to safety-service, so neither
 * an internal service credential nor a user id reaches the browser.
 */
export async function checkText(
  request: SafetyCheckRequest
): Promise<SafetyCheckResult> {
  const response = await fetch("/api/safety/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    // Fail closed. The caller must stop its intended LLM/storage operation and
    // present the always-visible Safety Center resources instead.
    return { flagLevel: "crisis", degraded: true, safetyEventId: null, support: null };
  }
  const result = (await response.json()) as {
    flag_level: SafetyCheckResult["flagLevel"];
    safety_event_id: string | null;
    support: SafetyCheckResult["support"];
  };
  return {
    flagLevel: result.flag_level,
    degraded: false,
    safetyEventId: result.safety_event_id,
    support: result.support,
  };
}
