"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { requestDataAction } from "@/lib/auth/actions";

interface DataRequestItem {
  id: string;
  request_type: "export" | "deletion";
  status: "pending" | "completed" | "denied";
  created_at: string;
  completed_at: string | null;
}

export function DataRequestSection({ initialRequests }: { initialRequests: DataRequestItem[] }) {
  const [requests, setRequests] = useState(initialRequests);
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const pendingExport = requests.some(
    (r) => r.request_type === "export" && r.status === "pending"
  );
  const pendingDeletion = requests.some(
    (r) => r.request_type === "deletion" && r.status === "pending"
  );

  function handleRequest(type: "export" | "deletion") {
    setError(null);
    startTransition(async () => {
      const formData = new FormData();
      formData.set("requestType", type);
      const result = await requestDataAction({}, formData);
      if (result.error) {
        setError(result.error);
        return;
      }
      // Optimistic row — a full reload will show the server's real id,
      // fine for this MVP since nothing else keys off this id client-side.
      setRequests((prev) => [
        {
          id: `optimistic-${Date.now()}`,
          request_type: type,
          status: "pending" as const,
          created_at: new Date().toISOString(),
          completed_at: null,
        },
        ...prev,
      ]);
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-ink-muted">
        Requesting either of these creates a record we follow up on manually for now
        — not yet an instant, automated process.
      </p>

      <div className="flex flex-col gap-2 sm:flex-row">
        <Button
          type="button"
          variant="secondary"
          disabled={isPending || pendingExport}
          onClick={() => handleRequest("export")}
        >
          {pendingExport ? "Export requested" : "Request my data"}
        </Button>
        <Button
          type="button"
          variant="quiet-destructive"
          disabled={isPending || pendingDeletion}
          onClick={() => handleRequest("deletion")}
        >
          {pendingDeletion ? "Deletion requested" : "Request account deletion"}
        </Button>
      </div>

      {error && (
        <p role="alert" className="text-sm text-clay">
          {error}
        </p>
      )}

      {requests.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-ink-muted">Request history</span>
          <ul className="flex flex-col gap-1.5">
            {requests.map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between rounded-md border border-border-subtle bg-paper-raised px-3 py-2 text-xs text-ink-muted"
              >
                <span className="capitalize">{r.request_type}</span>
                <span className="capitalize">{r.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
