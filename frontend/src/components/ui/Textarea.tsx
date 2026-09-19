import { forwardRef } from "react";
import { cn } from "@/lib/cn";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-24 w-full rounded-md border border-border bg-paper-raised px-3.5 py-2.5 text-sm text-ink placeholder:text-ink-muted",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "aria-[invalid=true]:border-clay",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";
