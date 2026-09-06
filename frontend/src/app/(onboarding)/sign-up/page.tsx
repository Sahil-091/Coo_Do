"use client";

import Link from "next/link";
import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { registerAction, type ActionState } from "@/lib/auth/actions";

const initialState: ActionState = {};

export default function SignUpPage() {
  const [state, formAction, isPending] = useActionState(registerAction, initialState);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">Create your account</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Just an email and password to start — everything else is optional.
        </p>
      </div>

      <form action={formAction} className="flex flex-col gap-4" noValidate>
        <FormField label="Email" error={state.fieldErrors?.email?.[0]} required>
          {(fieldProps) => (
            <Input type="email" name="email" autoComplete="email" {...fieldProps} />
          )}
        </FormField>

        <FormField
          label="Password"
          hint="At least 8 characters."
          error={state.fieldErrors?.password?.[0]}
          required
        >
          {(fieldProps) => (
            <Input type="password" name="password" autoComplete="new-password" {...fieldProps} />
          )}
        </FormField>

        {state.error && (
          <p role="alert" className="text-sm text-clay">
            {state.error}
          </p>
        )}

        <Button type="submit" disabled={isPending} className="mt-2">
          {isPending ? "Creating account…" : "Continue"}
        </Button>
      </form>

      <p className="text-center text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-ink underline underline-offset-2">
          Log in
        </Link>
      </p>
    </div>
  );
}
