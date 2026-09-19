import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { LocalMeetupsClient } from "./LocalMeetupsClient";
import type { Meetup, Venue } from "./actions";

export default async function LocalMeetupsPage() {
  const user = await requireOnboardedUser();
  let meetups: Meetup[] = [];
  let venues: Venue[] = [];
  try {
    [meetups, venues] = await Promise.all([
      internalApiFetch<Meetup[]>(`/internal/users/${user.userId}/meetups`),
      internalApiFetch<Venue[]>(`/internal/users/${user.userId}/meetup-venues`),
    ]);
  } catch {
    // The creation form fails closed when the verified server-owned venue
    // catalogue is unavailable; activity discovery itself can still render.
  }
  return <LocalMeetupsClient initialMeetups={meetups} venues={venues} />;
}
