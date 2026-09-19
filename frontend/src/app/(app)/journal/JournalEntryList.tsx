"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { deleteJournalEntryAction, type JournalExportEntry } from "./actions";

export function JournalEntryList({ entries }: { entries: JournalExportEntry[] }) {
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function permanentlyDelete(entryId: string) {
    setError(null);
    startTransition(async () => {
      const formData = new FormData();
      formData.set("entryId", entryId);
      const result = await deleteJournalEntryAction({}, formData);
      if (result.error) setError(result.error);
      else setConfirmingId(null);
    });
  }

  if (entries.length === 0) {
    return <p className="mt-3 text-sm text-ink-muted">Nothing here yet. A sentence about today is enough.</p>;
  }

  return <div className="mt-3 space-y-3">
    {error && <p role="alert" className="text-sm text-clay">{error}</p>}
    {entries.map((entry) => (
      <article key={entry.id} className="rounded-xl border border-border-subtle bg-white p-4">
        <time className="text-xs text-ink-muted">{new Date(entry.created_at).toLocaleString()}</time>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink">{entry.body}</p>
        {confirmingId === entry.id ? (
          <div className="mt-4 rounded-lg border border-clay/30 bg-clay-tint p-3">
            <p className="text-sm text-ink">Permanently delete this reflection? This cannot be undone.</p>
            <div className="mt-3 flex gap-2">
              <Button size="sm" variant="quiet-destructive" onClick={() => permanentlyDelete(entry.id)} disabled={isPending}>
                {isPending ? "Deleting…" : "Delete permanently"}
              </Button>
              <Button size="sm" variant="secondary" onClick={() => setConfirmingId(null)} disabled={isPending}>Cancel</Button>
            </div>
          </div>
        ) : (
          <Button size="sm" variant="quiet-destructive" className="mt-4" onClick={() => setConfirmingId(entry.id)} disabled={isPending}>
            Delete reflection
          </Button>
        )}
      </article>
    ))}
  </div>;
}
