"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { internalMatchingApiFetch } from "@/lib/matching-api-server";
import { mapProfile, type ApiProfile, type MatchingProfile, type ReportCategory } from "./types";

export async function updateMatchingProfileAction(payload: MatchingProfile): Promise<MatchingProfile | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const profile = await internalApiFetch<ApiProfile>(`/internal/users/${user.userId}/matching-profile`, {
      method: "PUT",
      body: JSON.stringify({ course: payload.course, year: payload.year, interests: payload.interests, activity_types: payload.activityTypes, region: payload.region, language: payload.language }),
    });
    return mapProfile(profile);
  } catch {
    return { error: "Couldn’t save your matching profile. Check the details and try again." };
  }
}

export async function requestMatchAction(targetUserId: string): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalMatchingApiFetch("/internal/matches/requests", { method: "POST", body: JSON.stringify({ user_id: user.userId, target_user_id: targetUserId }) });
    return {};
  } catch { return { error: "That connection is unavailable right now." }; }
}

export async function blockMatchAction(targetUserId: string): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalMatchingApiFetch("/internal/matches/block", { method: "POST", body: JSON.stringify({ user_id: user.userId, target_user_id: targetUserId }) });
    return {};
  } catch { return { error: "Couldn’t hide this profile. Please try again." }; }
}

export async function reportMatchAction(targetUserId: string, category: ReportCategory): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalMatchingApiFetch("/internal/matches/report", { method: "POST", body: JSON.stringify({ user_id: user.userId, target_user_id: targetUserId, category }) });
    return {};
  } catch { return { error: "Couldn’t send that report. Please try again." }; }
}
