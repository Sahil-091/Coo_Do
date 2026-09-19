"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { deleteAllJournalEntriesAction, exportJournalAction } from "./actions";

export function JournalControls({ hasEntries }: { hasEntries: boolean }) {
  const [confirmingDeleteAll, setConfirmingDeleteAll] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function exportJournal() {
    setError(null);
    startTransition(async () => {
      const result = await exportJournalAction();
      if (!result.entries) {
        setError(result.error ?? "Your journal export could not be prepared.");
        return;
      }
      const blob = new Blob([JSON.stringify({ exported_at: new Date().toISOString(), entries: result.entries }, null, 2)], { type: "application/json" });
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = "campus-connect-journal.json";
      link.click();
      URL.revokeObjectURL(href);
    });
  }

  function permanentlyDeleteAll() {
    setError(null);
    startTransition(async () => {
      const result = await deleteAllJournalEntriesAction({});
      if (result.error) setError(result.error);
      else setConfirmingDeleteAll(false);
    });
  }

  return <section className="rounded-xl border border-border-subtle bg-paper-raised p-5">
    <h2 className="font-display text-xl text-ink">Journal data</h2>
    <p className="mt-1 text-sm leading-6 text-ink-muted">Export your reflections as a file, or permanently delete them from this journal.</p>
    <div className="mt-4 flex flex-wrap gap-2">
      <Button variant="secondary" onClick={exportJournal} disabled={isPending}>{isPending ? "Preparing…" : "Export journal"}</Button>
      {hasEntries && !confirmingDeleteAll && <Button variant="quiet-destructive" onClick={() => setConfirmingDeleteAll(true)} disabled={isPending}>Delete all reflections</Button>}
    </div>
    {confirmingDeleteAll && <div className="mt-4 rounded-lg border border-clay/30 bg-clay-tint p-3">
      <p className="text-sm text-ink">Permanently delete every journal reflection? This cannot be undone.</p>
      <div className="mt-3 flex gap-2"><Button size="sm" variant="quiet-destructive" onClick={permanentlyDeleteAll} disabled={isPending}>{isPending ? "Deleting…" : "Delete all permanently"}</Button><Button size="sm" variant="secondary" onClick={() => setConfirmingDeleteAll(false)} disabled={isPending}>Cancel</Button></div>
    </div>}
    {error && <p role="alert" className="mt-3 text-sm text-clay">{error}</p>}
  </section>;
}
