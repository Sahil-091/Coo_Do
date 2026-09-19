import { requireAuthenticatedUser } from "@/lib/auth/dal";
import { DisplayNameForm } from "./DisplayNameForm";

export default async function DisplayNamePage() {
  await requireAuthenticatedUser();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">What should we call you?</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Totally optional — leave this blank and stay anonymous if you&rsquo;d rather.
        </p>
      </div>
      <DisplayNameForm />
    </div>
  );
}
