import { cn } from "@/lib/cn";

interface ChipOptionProps {
  type: "checkbox" | "radio";
  name: string;
  value: string;
  checked: boolean;
  onChange: (value: string) => void;
  children: React.ReactNode;
}

/**
 * Renders a real <input type="checkbox"|"radio">, visually hidden
 * (sr-only, not display:none — stays focusable and in the a11y tree),
 * wrapped in a label styled as the visible "chip". This gets full
 * native semantics for free: proper announcement, arrow-key navigation
 * within a radio group, space/enter toggling — none of which a custom
 * role="button"/aria-pressed reimplementation would get without extra
 * hand-written keyboard handling.
 */
export function ChipOption({ type, name, value, checked, onChange, children }: ChipOptionProps) {
  return (
    <label
      className={cn(
        "cursor-pointer select-none rounded-full border px-4 py-2 text-sm transition-colors",
        "has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-lamp",
        checked
          ? "border-lamp bg-lamp-tint font-medium text-ink"
          : "border-border-subtle bg-paper-raised text-ink-muted hover:border-border hover:text-ink"
      )}
    >
      <input
        type={type}
        name={name}
        value={value}
        checked={checked}
        onChange={() => onChange(value)}
        className="sr-only"
      />
      {children}
    </label>
  );
}
