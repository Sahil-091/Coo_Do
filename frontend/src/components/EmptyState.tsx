import type { LucideIcon } from "lucide-react";

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  phaseNote?: string;
}

/** Per the writing guidance: an empty screen is an invitation to act,
 * not an apology. Every consumer must give a specific title/description
 * — no "No data yet" placeholders. */
export function EmptyState({ icon: Icon, title, description, phaseNote }: EmptyStateProps) {
  return (
    <div className="flex max-w-md flex-col items-start gap-3 py-6">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-lamp-tint">
        <Icon className="h-6 w-6 text-lamp" aria-hidden="true" />
      </span>
      <h1 className="font-display text-2xl text-ink">{title}</h1>
      <p className="text-sm text-ink-muted">{description}</p>
      {phaseNote && (
        <span className="rounded-full border border-border-subtle px-3 py-1 text-xs text-ink-muted">
          {phaseNote}
        </span>
      )}
    </div>
  );
}
