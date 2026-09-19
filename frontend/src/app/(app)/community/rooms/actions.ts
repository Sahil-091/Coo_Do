"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalModerationApiFetch } from "@/lib/moderation-api-server";
import { mapPost, mapRoom, type CommunityPost, type CommunityReportCategory, type SituationRoom, type SituationTopic } from "./types";

export async function createSituationRoomAction(topic: SituationTopic): Promise<SituationRoom | { error: string }> {
  const user = await requireOnboardedUser();
  try { return mapRoom(await internalModerationApiFetch("/internal/community/rooms", { method: "POST", body: JSON.stringify({ user_id: user.userId, topic }) })); }
  catch { return { error: "Couldn’t create that room right now. Please try again later." }; }
}

export async function acceptCommunityGuidelinesAction(): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try { await internalModerationApiFetch("/internal/community/guidelines/accept", { method: "POST", body: JSON.stringify({ user_id: user.userId, guidelines_version: "community-guidelines-v1" }) }); return {}; }
  catch { return { error: "Couldn’t save your acknowledgement. Please try again." }; }
}

export async function loadCommunityPostsAction(roomId: string): Promise<CommunityPost[] | { error: string }> {
  await requireOnboardedUser();
  try { const posts = await internalModerationApiFetch<unknown[]>(`/internal/community/rooms/${encodeURIComponent(roomId)}/posts`); return posts.map((post) => mapPost(post as Parameters<typeof mapPost>[0])); }
  catch { return { error: "Couldn’t load this room right now." }; }
}

export async function submitCommunityPostAction(roomId: string, body: string): Promise<{ post?: CommunityPost; heldForReview?: boolean; safetyFlagLevel?: string; error?: string }> {
  const user = await requireOnboardedUser();
  try {
    const result = await internalModerationApiFetch<{ post: Parameters<typeof mapPost>[0] | null; held_for_review: boolean; safety_flag_level: string }>(`/internal/community/rooms/${encodeURIComponent(roomId)}/posts`, { method: "POST", body: JSON.stringify({ user_id: user.userId, body, guidelines_version: "community-guidelines-v1" }) });
    return { post: result.post ? mapPost(result.post) : undefined, heldForReview: result.held_for_review, safetyFlagLevel: result.safety_flag_level };
  } catch { return { error: "Your post wasn’t shared. Safety screening may be temporarily unavailable—please try again or use the resources below." }; }
}

export async function reportCommunityPostAction(postId: string, category: CommunityReportCategory): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try { await internalModerationApiFetch(`/internal/community/posts/${encodeURIComponent(postId)}/reports`, { method: "POST", body: JSON.stringify({ user_id: user.userId, category }) }); return {}; }
  catch { return { error: "Couldn’t send that report. Please try again." }; }
}
