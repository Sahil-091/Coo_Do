"use server";

import { revalidatePath } from "next/cache";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { reviewerModerationApiFetch } from "@/lib/moderation-api-server";
import { serverEnv } from "@/lib/env.server";

const DECISIONS = new Set(["approved", "removed"]);

function isAllowedModerator(email: string): boolean {
  return serverEnv.MODERATION_REVIEWER_EMAILS?.split(",")
    .map((item) => item.trim().toLowerCase())
    .includes(email.toLowerCase()) ?? false;
}

/** Review authorization is repeated here because Server Actions are public POST endpoints. */
export async function decideModerationEvent(eventId: string, decision: string): Promise<void> {
  const reviewer = await requireOnboardedUser();
  if (!isAllowedModerator(reviewer.email)) throw new Error("Not authorized to review community posts.");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(eventId)) {
    throw new Error("Invalid moderation event.");
  }
  if (!DECISIONS.has(decision)) throw new Error("Invalid moderation decision.");

  await reviewerModerationApiFetch(`/internal/review/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify({ reviewer_ref: reviewer.userId, decision }),
  });
  revalidatePath("/community/review");
}
