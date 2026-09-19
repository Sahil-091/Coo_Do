"use client";

import { useId } from "react";

interface FormFieldProps {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: (fieldProps: {
    id: string;
    "aria-describedby": string | undefined;
    "aria-invalid": boolean;
    "aria-required": boolean | undefined;
  }) => React.ReactNode;
}

/**
 * Wraps a single form control (Input/Textarea) with a properly
 * associated label, optional hint, and optional error message — the
 * consumer never has to hand-wire id/aria-describedby/aria-invalid
 * themselves, which is where accessibility bugs usually creep in.
 *
 * Usage:
 *   <FormField label="What's on your mind?" hint="Optional">
 *     {(fieldProps) => <Textarea {...fieldProps} />}
 *   </FormField>
 */
export function FormField({ label, hint, error, required, children }: FormFieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-ink">
        {label}
        {required && (
          <span aria-hidden="true" className="text-clay">
            {" "}
            *
          </span>
        )}
      </label>
      {children({
        id,
        "aria-describedby": describedBy,
        "aria-invalid": Boolean(error),
        "aria-required": required,
      })}
      {hint && !error && (
        <p id={hintId} className="text-xs text-ink-muted">
          {hint}
        </p>
      )}
      {error && (
        <p id={errorId} role="alert" className="text-xs text-clay">
          {error}
        </p>
      )}
    </div>
  );
}
