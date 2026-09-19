"use client";
import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { createJournalEntryAction } from "./actions";
export function JournalComposer() { const [state, action, pending] = useActionState(createJournalEntryAction, {}); return <form action={action} className="rounded-xl border border-border-subtle bg-white p-5"><label className="text-sm font-semibold text-ink" htmlFor="journal-body">A thought from today</label><Textarea id="journal-body" name="body" className="mt-2" maxLength={10000} placeholder="Write as much or as little as you want…" required /><div className="mt-3 flex items-center gap-3"><Button type="submit" disabled={pending}>{pending ? "Saving…" : "Save privately"}</Button>{state.error && <p role="alert" className="text-sm text-clay">{state.error}</p>}</div></form>; }
