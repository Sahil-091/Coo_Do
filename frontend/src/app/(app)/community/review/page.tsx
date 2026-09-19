import { notFound } from "next/navigation";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { serverEnv } from "@/lib/env.server";
import { reviewerModerationApiFetch } from "@/lib/moderation-api-server";
import { decideModerationEvent } from "./actions";

interface ModerationEvent {
  id: string;
  post_id: string;
  room_id: string;
  body: string;
  reasons: string[];
  self_harm_level: string;
  review_status: "pending" | "approved" | "removed";
  created_at: string;
}

function allowedModerator(email: string): boolean {
  return serverEnv.MODERATION_REVIEWER_EMAILS?.split(",")
    .map((item) => item.trim().toLowerCase())
    .includes(email.toLowerCase()) ?? false;
}

/** Separate queue for Phase 12 community content; this is not the safety-events queue. */
export default async function CommunityModerationReviewPage() {
  const user = await requireOnboardedUser();
  if (!allowedModerator(user.email)) notFound();

  let events: ModerationEvent[] = [];
  let unavailable = false;
  try {
    events = await reviewerModerationApiFetch<ModerationEvent[]>("/internal/review/events");
  } catch {
    unavailable = true;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <header>
        <p className="text-sm font-semibold text-lamp">ROLE-GATED MODERATION</p>
        <h1 className="mt-1 font-display text-3xl text-ink">Community review queue</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-muted">
          Held posts remain invisible until a separately authorized reviewer approves or removes them.
        </p>
      </header>
      {unavailable ? (
        <p role="alert" className="rounded-lg bg-clay-tint p-4 text-sm text-clay">
          The moderation queue is unavailable or not configured. Do not treat held posts as reviewed.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-border-subtle bg-white">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="border-b border-border-subtle bg-paper">
              <tr>
                <th className="p-4">Held post</th><th className="p-4">Reasons</th><th className="p-4">Safety screen</th><th className="p-4">Created</th><th className="p-4"><span className="sr-only">Review actions</span></th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-b border-border-subtle align-top last:border-0">
                  <td className="max-w-md whitespace-pre-wrap p-4 leading-6 text-ink">{event.body}</td>
                  <td className="p-4 text-ink-muted">{event.reasons.join(", ")}</td>
                  <td className="p-4 text-ink-muted">{event.self_harm_level}</td>
                  <td className="whitespace-nowrap p-4 text-ink-muted">{new Date(event.created_at).toLocaleString()}</td>
                  <td className="p-4"><div className="flex gap-2"><form action={decideModerationEvent.bind(null, event.id, "approved")}><button type="submit" className="rounded-md border border-border-subtle px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper">Approve</button></form><form action={decideModerationEvent.bind(null, event.id, "removed")}><button type="submit" className="rounded-md bg-clay px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90">Remove</button></form></div></td>
                </tr>
              ))}
              {events.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-ink-muted">No community posts are waiting for review.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
