"use server";

import { revalidatePath } from "next/cache";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { serverEnv } from "@/lib/env.server";
import { reviewerSafetyFetch } from "@/lib/safety-server";

const OUTCOMES = new Set(["human_reviewed", "resolved"]);

function isAllowedReviewer(email: string): boolean {
  return (
    serverEnv.SAFETY_REVIEWER_EMAILS?.split(",")
      .map((item) => item.trim().toLowerCase())
      .includes(email.toLowerCase()) ?? false
  );
}

/**
 * The server action re-checks both identity and reviewer authorization. Rendering
 * the controls only to reviewers is helpful UX, but is not an authorization boundary.
 */
export async function recordReviewOutcome(eventId: string, outcome: string): Promise<void> {
  const reviewer = await requireOnboardedUser();
  if (!isAllowedReviewer(reviewer.email)) throw new Error("Not authorized to review safety events.");
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(eventId)) {
    throw new Error("Invalid safety event.");
  }
  if (!OUTCOMES.has(outcome)) throw new Error("Invalid review outcome.");

  await reviewerSafetyFetch(`/internal/review/events/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify({ reviewer_ref: reviewer.userId, escalation_status: outcome }),
  });
  revalidatePath("/safety/review");
}
