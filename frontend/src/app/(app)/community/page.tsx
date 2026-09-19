import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { CommunityClient } from "./CommunityClient";
import Link from "next/link";
import type { ActivityRoom, ActivityTopic } from "./actions";

interface ApiActivityRoom { id: string; topic: ActivityTopic; status: ActivityRoom["status"]; starts_at: string | null; ends_at: string | null; room_id: string; headcount: number; is_open: boolean; }

export default async function CommunityPage() {
  const user = await requireOnboardedUser();
  let initialActivities: ActivityRoom[] = [];
  try {
    const rooms = await internalApiFetch<ApiActivityRoom[]>(`/internal/users/${user.userId}/activities`);
    initialActivities = rooms.map((room) => ({ id: room.id, topic: room.topic, status: room.status, startsAt: room.starts_at, endsAt: room.ends_at, roomId: room.room_id, headcount: room.headcount, isOpen: room.is_open }));
  } catch {
    // The interactive page stays useful if the room listing has a short outage.
  }
  return <><CommunityClient initialActivities={initialActivities} /><section className="mx-auto mt-2 max-w-4xl rounded-xl border border-border-subtle bg-paper-raised p-5"><h2 className="font-display text-xl text-ink">Find a public-venue activity</h2><p className="mt-1 text-sm text-ink-muted">Discover activities in your server-coarsened area—never individual locations or attendee lists.</p><Link className="mt-3 inline-block text-sm font-semibold text-lamp underline" href="/community/local">Explore local activities</Link></section><section className="mx-auto mt-2 max-w-4xl rounded-xl border border-border-subtle bg-paper-raised p-5"><h2 className="font-display text-xl text-ink">Need a place to talk anonymously?</h2><p className="mt-1 text-sm text-ink-muted">Situation rooms are topic-based, screened before posts appear, and always show crisis resources.</p><Link className="mt-3 inline-block text-sm font-semibold text-lamp underline" href="/community/rooms">Explore anonymous situation rooms</Link></section></>;
}
