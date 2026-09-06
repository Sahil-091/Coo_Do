/**
 * Shared contract between the frontend and the safety-service backend.
 * See R&D doc Section 10 (AI Architecture) and Section 14 (Crisis System).
 *
 * This file defines the SHAPE of a safety check only. The actual
 * classification happens server-side in /backend/services/safety-service.
 * Nothing in this file should contain detection logic.
 */

export type SafetyFlagLevel = "none" | "elevated" | "crisis";

export interface SafetyCheckRequest {
  /** Raw user text to be screened before it reaches any LLM call or storage. */
  text: string;
  /** Where the text originated, for audit/logging purposes only. */
  source: "checkin_freetext" | "ai_navigator" | "community_post" | "journal";
}

export interface SafetyCheckResult {
  flagLevel: SafetyFlagLevel;
  /** True if the safety-service could not be reached; caller must fail safe. */
  degraded: boolean;
  /** Opaque id for the logged safety_event row, if one was created. Never log raw text client-side. */
  safetyEventId: string | null;
}
