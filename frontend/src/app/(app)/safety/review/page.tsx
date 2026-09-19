import { notFound } from "next/navigation";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { serverEnv } from "@/lib/env.server";
import { reviewerSafetyFetch } from "@/lib/safety-server";
import { recordReviewOutcome } from "./actions";

interface ReviewEvent { id: string; user_ref: string; flag_level: string; source: string; response_template_id: string; classifier_model: string; classifier_prompt_version: string; escalation_status: string; created_at: string; reviewed_at: string | null }

function allowedReviewer(email: string) {
  return serverEnv.SAFETY_REVIEWER_EMAILS?.split(",").map((item) => item.trim().toLowerCase()).includes(email.toLowerCase()) ?? false;
}

export default async function SafetyReviewPage() {
  const user = await requireOnboardedUser();
  if (!allowedReviewer(user.email)) notFound();
  let events: ReviewEvent[] = [];
  let unavailable = false;
  try { events = await reviewerSafetyFetch<ReviewEvent[]>("/internal/review/events"); } catch { unavailable = true; }
  return <div className="mx-auto max-w-5xl space-y-5"><div><h1 className="text-3xl font-bold tracking-tight text-ink">Safety review</h1><p className="mt-2 text-sm text-ink-muted">Flag metadata only. Raw crisis text is intentionally not shown to this reviewer role.</p></div>{unavailable ? <p role="alert" className="rounded-lg bg-clay-tint p-4 text-sm text-clay">The review queue is unavailable or not configured.</p> : <div className="overflow-x-auto rounded-2xl border border-border-subtle bg-white"><table className="w-full min-w-[840px] text-left text-sm"><thead className="border-b border-border-subtle bg-paper"><tr><th className="p-4">Flag</th><th className="p-4">Source</th><th className="p-4">Status</th><th className="p-4">Classifier audit</th><th className="p-4">Created</th><th className="p-4"><span className="sr-only">Review actions</span></th></tr></thead><tbody>{events.map((event) => <tr key={event.id} className="border-b border-border-subtle last:border-0"><td className="p-4 font-semibold text-ink">{event.flag_level}</td><td className="p-4 text-ink-muted">{event.source}</td><td className="p-4 text-ink-muted">{event.escalation_status}</td><td className="p-4 text-xs text-ink-muted">{event.classifier_model}<br />{event.classifier_prompt_version}</td><td className="p-4 text-ink-muted">{new Date(event.created_at).toLocaleString()}</td><td className="p-4"><div className="flex gap-2">{event.escalation_status === "human_review_pending" && <form action={recordReviewOutcome.bind(null, event.id, "human_reviewed")}><button type="submit" className="rounded-md border border-border-subtle px-3 py-1.5 text-xs font-semibold text-ink hover:bg-paper">Mark reviewed</button></form>}{event.escalation_status !== "resolved" && <form action={recordReviewOutcome.bind(null, event.id, "resolved")}><button type="submit" className="rounded-md bg-lamp px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90">Resolve</button></form>}</div></td></tr>)}{events.length === 0 && <tr><td colSpan={6} className="p-8 text-center text-ink-muted">No flagged events are waiting for review.</td></tr>}</tbody></table></div>}</div>;
}
