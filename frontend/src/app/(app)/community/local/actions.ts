"use server";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";

export type Meetup = { id: string; title: string; description: string; category: string; venue_name: string; venue_map_url: string; starts_at: string; max_participants: number; joining_count: number; maybe_count: number; my_rsvp: "joining" | "maybe" | "ignored" | null };
export type Venue = { id: string; name: string; category: string; map_url: string };

export async function rsvpMeetupAction(id: string, status: "joining" | "maybe" | "ignored"): Promise<Meetup | { error: string }> {
  const user = await requireOnboardedUser();
  try { return await internalApiFetch<Meetup>(`/internal/users/${user.userId}/meetups/${encodeURIComponent(id)}/rsvp`, { method: "PUT", body: JSON.stringify({ status }) }); }
  catch { return { error: "Couldn’t update your RSVP. Please try again." }; }
}

export async function setActivityAreaAction(latitude: number, longitude: number): Promise<{ error?: string }> { const user = await requireOnboardedUser(); try { await internalApiFetch(`/internal/users/${user.userId}/activity-alert-preference`, { method: "PUT", body: JSON.stringify({ latitude, longitude, enabled: true }) }); return {}; } catch { return { error: "Enable Local activity alerts in Settings first, then try again." }; } }

export async function clearActivityAreaAction(): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalApiFetch(`/internal/users/${user.userId}/activity-alert-preference`, {
      method: "PUT",
      body: JSON.stringify({ enabled: false }),
    });
    return {};
  } catch {
    return { error: "Couldn’t clear your activity area. Please try again." };
  }
}

export async function createMeetupAction(payload: { title: string; description: string; category: string; venue_id: string; starts_at: string; max_participants: number }): Promise<Meetup | { error: string }> { const user = await requireOnboardedUser(); try { return await internalApiFetch<Meetup>(`/internal/users/${user.userId}/meetups`, { method: "POST", body: JSON.stringify(payload) }); } catch { return { error: "Couldn’t publish this activity. Check the details and try again." }; } }
