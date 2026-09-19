export type ActivityType = "study" | "coding" | "reading" | "writing" | "quiet_work";
export type ReportCategory = "dating_or_romantic_approach" | "harassment" | "safety_concern" | "other";

export interface MatchingProfile {
  course: string | null;
  year: number | null;
  interests: string[];
  activityTypes: ActivityType[];
  region: string | null;
  language: string | null;
}

export interface MatchCandidate {
  userId: string;
  displayName: string | null;
  course: string | null;
  year: number | null;
  sharedInterests: string[];
  sharedActivityTypes: ActivityType[];
  sameCourse: boolean;
  sameYear: boolean;
  compatibilityReason: string;
}

export interface ApiProfile {
  course: string | null; year: number | null; interests: string[];
  activity_types: ActivityType[]; region: string | null; language: string | null;
}
export interface ApiCandidate {
  user_id: string; display_name: string | null; course: string | null; year: number | null;
  shared_interests: string[]; shared_activity_types: ActivityType[];
  same_course: boolean; same_year: boolean; compatibility_reason: string;
}

export function mapProfile(profile: ApiProfile): MatchingProfile {
  return { course: profile.course, year: profile.year, interests: profile.interests, activityTypes: profile.activity_types, region: profile.region, language: profile.language };
}
export function mapCandidate(candidate: ApiCandidate): MatchCandidate {
  return { userId: candidate.user_id, displayName: candidate.display_name, course: candidate.course, year: candidate.year, sharedInterests: candidate.shared_interests, sharedActivityTypes: candidate.shared_activity_types, sameCourse: candidate.same_course, sameYear: candidate.same_year, compatibilityReason: candidate.compatibility_reason };
}
