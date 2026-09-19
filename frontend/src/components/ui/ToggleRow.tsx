import { cn } from "@/lib/cn";

interface ToggleRowProps {
  title: string;
  description: string;
  checked: boolean;
  onCheckedChange: () => void;
  disabled?: boolean;
  error?: string;
}

export function ToggleRow({
  title,
  description,
  checked,
  onCheckedChange,
  disabled,
  error,
}: ToggleRowProps) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-border-subtle bg-paper-raised p-4">
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-ink">{title}</span>
        <span className="text-xs text-ink-muted">{description}</span>
        {error && (
          <span role="alert" className="text-xs text-clay">
            {error}
          </span>
        )}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={title}
        onClick={onCheckedChange}
        disabled={disabled}
        className={cn(
          "relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-60",
          checked ? "bg-lamp" : "bg-border"
        )}
      >
        <span
          aria-hidden="true"
          className={cn(
            "absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform",
            checked ? "translate-x-5" : "translate-x-0.5"
          )}
        />
      </button>
    </div>
  );
}
