import { forwardRef } from "react";
import { cn } from "@/lib/cn";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn(
          "h-11 w-full rounded-md border border-border bg-paper-raised px-3.5 text-sm text-ink placeholder:text-ink-muted",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "aria-[invalid=true]:border-clay",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
