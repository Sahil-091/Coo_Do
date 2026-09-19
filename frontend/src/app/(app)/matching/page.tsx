import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { internalMatchingApiFetch } from "@/lib/matching-api-server";
import { mapCandidate, mapProfile, type ApiCandidate, type ApiProfile, type MatchCandidate, type MatchingProfile } from "./types";
import { MatchingClient } from "./MatchingClient";

interface Consent { consent_type: string; granted: boolean; }
interface Privacy { profile_visible_in_matching: boolean; }

export default async function MatchingPage() {
  const user = await requireOnboardedUser();
  const [profileResult, consentResult, privacyResult] = await Promise.allSettled([
    internalApiFetch(`/internal/users/${user.userId}/matching-profile`),
    internalApiFetch<Consent[]>(`/internal/users/${user.userId}/consents`),
    internalApiFetch<Privacy>(`/internal/users/${user.userId}/privacy-settings`),
  ]);
  const profile: MatchingProfile = profileResult.status === "fulfilled" ? mapProfile(profileResult.value as ApiProfile) : { course: null, year: null, interests: [], activityTypes: [], region: null, language: null };
  const consented = consentResult.status === "fulfilled" && consentResult.value.some((item) => item.consent_type === "matching_visibility" && item.granted);
  const visible = privacyResult.status === "fulfilled" && privacyResult.value.profile_visible_in_matching;
  let candidates: MatchCandidate[] = [];
  if (consented && visible) {
    try {
      const rows = await internalMatchingApiFetch<unknown[]>(`/internal/matches?user_id=${encodeURIComponent(user.userId)}`);
      candidates = rows.map((row) => mapCandidate(row as ApiCandidate));
    } catch {
      // The edit form remains available if matching is briefly unavailable.
    }
  }
  return <MatchingClient initialProfile={profile} initialCandidates={candidates} isEnabled={consented && visible} />;
}
