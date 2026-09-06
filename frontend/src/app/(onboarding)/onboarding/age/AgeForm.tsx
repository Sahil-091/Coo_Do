"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { submitAgeAction, type ActionState } from "@/lib/auth/actions";

const initialState: ActionState & { ageVerified?: boolean } = {};

export function AgeForm() {
  const [state, formAction, isPending] = useActionState(submitAgeAction, initialState);

  if (state.ageVerified === false) {
    return (
      <div className="flex flex-col gap-3 rounded-lg border border-border-subtle bg-paper-raised p-5">
        <h2 className="font-display text-lg text-ink">Not quite yet</h2>
        <p className="text-sm text-ink-muted">
          This early version of Campus Connect is only available to students 18 and
          over. We know that&rsquo;s not the answer you wanted — if you&rsquo;re
          struggling right now, please reach out to a trusted adult, a school
          counselor, or a helpline in your country. You&rsquo;re not alone in this,
          even though this particular app can&rsquo;t be part of it yet.
        </p>
      </div>
    );
  }

  return (
    <form action={formAction} className="flex flex-col gap-4" noValidate>
      <FormField
        label="Date of birth"
        hint="This app is currently available to students 18 and older."
        error={state.fieldErrors?.dateOfBirth?.[0]}
        required
      >
        {(fieldProps) => <Input type="date" name="dateOfBirth" {...fieldProps} />}
      </FormField>

      {state.error && (
        <p role="alert" className="text-sm text-clay">
          {state.error}
        </p>
      )}

      <Button type="submit" disabled={isPending} className="mt-2">
        {isPending ? "Checking…" : "Continue"}
      </Button>
    </form>
  );
}
