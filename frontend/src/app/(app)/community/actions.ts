"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";

export type ActivityTopic = "study" | "coding" | "reading" | "writing" | "quiet_work";

export interface ActivityRoom {
  id: string;
  topic: ActivityTopic;
  status: "scheduled" | "live" | "closed";
  startsAt: string | null;
  endsAt: string | null;
  roomId: string;
  headcount: number;
  isOpen: boolean;
}

interface ApiActivityRoom {
  id: string;
  topic: ActivityTopic;
  status: ActivityRoom["status"];
  starts_at: string | null;
  ends_at: string | null;
  room_id: string;
  headcount: number;
  is_open: boolean;
}

function mapActivity(room: ApiActivityRoom): ActivityRoom {
  return {
    id: room.id,
    topic: room.topic,
    status: room.status,
    startsAt: room.starts_at,
    endsAt: room.ends_at,
    roomId: room.room_id,
    headcount: room.headcount,
    isOpen: room.is_open,
  };
}

export async function createActivityAction(
  topic: ActivityTopic,
  scheduledFor?: string
): Promise<ActivityRoom | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const room = await internalApiFetch<ApiActivityRoom>(`/internal/users/${user.userId}/activities`, {
      method: "POST",
      body: JSON.stringify({ topic, starts_at: scheduledFor ? new Date(scheduledFor).toISOString() : null }),
    });
    return mapActivity(room);
  } catch {
    return { error: "Couldn’t create that room right now. Please try again later." };
  }
}

export async function joinActivityAction(activityId: string): Promise<
  { roomId: string; token: string; headcount: number } | { error: string }
> {
  const user = await requireOnboardedUser();
  try {
    const result = await internalApiFetch<{ room_id: string; websocket_token: string; headcount: number }>(
      `/internal/users/${user.userId}/activities/${activityId}/presence-token`,
      { method: "POST" }
    );
    return { roomId: result.room_id, token: result.websocket_token, headcount: result.headcount };
  } catch {
    return { error: "Couldn’t join that room right now. It may not have started yet." };
  }
}

export async function savePresenceFeedbackAction(
  activityId: string,
  feedback: "less_alone" | "neutral" | "not_for_me" | null
): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalApiFetch<void>(`/internal/users/${user.userId}/activities/${activityId}/presence-feedback`, {
      method: "PUT",
      body: JSON.stringify({ feedback }),
    });
    return {};
  } catch {
    return { error: "Couldn’t save that response. Nothing else was affected." };
  }
}
