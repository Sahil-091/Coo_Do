"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import type { SuggestedPath } from "./types";
import { checkInSchema } from "./validation";

export interface CheckInActionState {
  error?: string;
  result?: {
    path: SuggestedPath;
    reason: string;
    checkinId: string;
  };
}

interface CheckInSubmitResponse {
  checkin: { id: string; feelings: string[]; stated_need: string; created_at: string };
  routing: { path: SuggestedPath; reason: string };
}

/**
 * `timeOfDay` MUST arrive already computed by the caller (see
 * lib/checkin/time-of-day.ts) from the student's own local clock —
 * this Server Action runs on the server, so calling `new Date()` in
 * here would silently use the server's timezone instead of the
 * student's, which would quietly break the "lonely at night" routing
 * modifier for anyone not in the server's timezone.
 */
export async function submitCheckInAction(
  _prevState: CheckInActionState,
  formData: FormData
): Promise<CheckInActionState> {
  const user = await requireOnboardedUser();

  const parsed = checkInSchema.safeParse({
    feelings: formData.getAll("feelings"),
    statedNeed: formData.get("statedNeed"),
    timeOfDay: formData.get("timeOfDay"),
  });

  if (!parsed.success) {
    return { error: "Please select at least one feeling and what you need." };
  }

  try {
    const response = await internalApiFetch<CheckInSubmitResponse>(
      `/internal/users/${user.userId}/checkins`,
      {
        method: "POST",
        body: JSON.stringify({
          feelings: parsed.data.feelings,
          stated_need: parsed.data.statedNeed,
          time_of_day: parsed.data.timeOfDay,
        }),
      }
    );

    return { result: { ...response.routing, checkinId: response.checkin.id } };
  } catch {
    return { error: "Something went wrong saving your check-in. Please try again." };
  }
}
