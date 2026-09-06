import { requireAuthenticatedUser } from "@/lib/auth/dal";
import { AgeForm } from "./AgeForm";

export default async function AgeVerificationPage() {
  await requireAuthenticatedUser();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">How old are you?</h1>
        <p className="mt-1 text-sm text-ink-muted">
          One quick, honest check before we continue.
        </p>
      </div>
      <AgeForm />
    </div>
  );
}
