/**
 * Shared domain types mirroring the Phase-0 backend schema
 * (R&D doc Section 19). These will evolve as each feature phase lands —
 * treat this file as a living contract, not a final spec.
 */

export interface UserProfile {
  id: string;
  pseudonymousDisplayName: string | null;
  ageVerified: boolean;
  createdAt: string;
}

export interface CheckIn {
  id: string;
  userId: string;
  feelings: string[];
  statedNeed: string | null;
  createdAt: string;
}

export interface TinyAction {
  id: string;
  category: string;
  difficultyLevel: number;
  ladderParentId: string | null;
  title: string;
  description: string;
}

export type ActionAttemptStatus = "suggested" | "completed" | "skipped" | "reduced";

export interface ActionAttempt {
  id: string;
  userId: string;
  tinyActionId: string;
  status: ActionAttemptStatus;
  relatedCheckInId: string | null;
  createdAt: string;
}

export type ConsentType =
  | "ai_chat"
  | "anonymous_community"
  | "matching_visibility"
  | "institutional_data_sharing";

export interface ConsentRecord {
  id: string;
  userId: string;
  consentType: ConsentType;
  granted: boolean;
  grantedAt: string;
}
