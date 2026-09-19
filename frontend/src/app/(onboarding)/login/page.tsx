"use client";

import Link from "next/link";
import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input } from "@/components/ui/Input";
import { loginAction, type ActionState } from "@/lib/auth/actions";

const initialState: ActionState = {};

export default function LoginPage() {
  const [state, formAction, isPending] = useActionState(loginAction, initialState);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">Welcome back</h1>
        <p className="mt-1 text-sm text-ink-muted">Log in to pick up where you left off.</p>
      </div>

      <form action={formAction} className="flex flex-col gap-4" noValidate>
        <FormField label="Email" error={state.fieldErrors?.email?.[0]} required>
          {(fieldProps) => (
            <Input type="email" name="email" autoComplete="email" {...fieldProps} />
          )}
        </FormField>

        <FormField label="Password" error={state.fieldErrors?.password?.[0]} required>
          {(fieldProps) => (
            <Input
              type="password"
              name="password"
              autoComplete="current-password"
              {...fieldProps}
            />
          )}
        </FormField>

        {state.error && (
          <p role="alert" className="text-sm text-clay">
            {state.error}
          </p>
        )}

        <Button type="submit" disabled={isPending} className="mt-2">
          {isPending ? "Logging in…" : "Log in"}
        </Button>
      </form>

      <p className="text-center text-sm text-ink-muted">
        New here?{" "}
        <Link href="/sign-up" className="font-medium text-ink underline underline-offset-2">
          Create an account
        </Link>
      </p>
    </div>
  );
}
