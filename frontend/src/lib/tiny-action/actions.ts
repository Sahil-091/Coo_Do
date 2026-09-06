"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import type { AttemptStatus, TinyActionRung } from "./types";

interface SuggestionApiResponse {
  ladder: { id: string; difficulty_level: number; title: string; description: string }[];
  suggested_attempt_id: string;
}

export interface SuggestionResult {
  ladder: TinyActionRung[];
  suggestedAttemptId: string;
}

function mapSuggestion(api: SuggestionApiResponse): SuggestionResult {
  return {
    ladder: api.ladder.map((r) => ({
      id: r.id,
      difficultyLevel: r.difficulty_level,
      title: r.title,
      description: r.description,
    })),
    suggestedAttemptId: api.suggested_attempt_id,
  };
}

export async function getSuggestionAction(): Promise<SuggestionResult | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const response = await internalApiFetch<SuggestionApiResponse>(
      `/internal/users/${user.userId}/tiny-actions/suggestion`
    );
    return mapSuggestion(response);
  } catch {
    return { error: "Couldn't load a suggestion right now. Please try again." };
  }
}

export interface LogAttemptResult {
  showSupportNudge: boolean;
}

export async function logAttemptAction(
  tinyActionId: string,
  status: AttemptStatus,
  checkinId?: string
): Promise<LogAttemptResult | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const response = await internalApiFetch<{ show_support_nudge: boolean }>(
      `/internal/users/${user.userId}/action-attempts`,
      {
        method: "POST",
        body: JSON.stringify({
          tiny_action_id: tinyActionId,
          status,
          related_checkin_id: checkinId ?? null,
        }),
      }
    );
    return { showSupportNudge: response.show_support_nudge };
  } catch {
    return { error: "Couldn't save that. Please try again." };
  }
}
