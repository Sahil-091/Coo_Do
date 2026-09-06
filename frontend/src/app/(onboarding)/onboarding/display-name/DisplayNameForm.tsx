"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { submitDisplayNameAction, type ActionState } from "@/lib/auth/actions";

const initialState: ActionState = {};

export function DisplayNameForm() {
  const [state, formAction, isPending] = useActionState(submitDisplayNameAction, initialState);

  return (
    <form action={formAction} className="flex flex-col gap-4" noValidate>
      <FormField
        label="Display name (optional)"
        hint="Shown to other students if you join a room or activity — never your email or real name unless you choose to share it."
        error={state.fieldErrors?.displayName?.[0]}
      >
        {(fieldProps) => <Input type="text" name="displayName" placeholder="e.g. Quiet Fox" {...fieldProps} />}
      </FormField>

      {state.error && (
        <p role="alert" className="text-sm text-clay">
          {state.error}
        </p>
      )}

      <Button type="submit" disabled={isPending} className="mt-2">
        {isPending ? "Saving…" : "Continue"}
      </Button>
    </form>
  );
}
