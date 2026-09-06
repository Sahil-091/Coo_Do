import { Button } from "@/components/ui/Button";
import { ConsentToggle } from "@/components/ConsentToggle";
import { completeOnboardingAction } from "@/lib/auth/actions";
import { requireAuthenticatedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { CONSENT_ITEMS } from "@/lib/consent-config";

interface ConsentStateResponse {
  consent_type: string;
  granted: boolean;
  updated_at: string | null;
}

export default async function ConsentPage() {
  const user = await requireAuthenticatedUser();
  const consents = await internalApiFetch<ConsentStateResponse[]>(
    `/internal/users/${user.userId}/consents`
  );
  const grantedByType = Object.fromEntries(consents.map((c) => [c.consent_type, c.granted]));

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">Your choices</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Everything below is off by default. Turn on only what you want — you can
          change any of these anytime in Settings.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {CONSENT_ITEMS.map((item) => (
          <ConsentToggle
            key={item.type}
            consentType={item.type}
            title={item.title}
            description={item.description}
            initialGranted={grantedByType[item.type] ?? false}
          />
        ))}
      </div>

      <form action={completeOnboardingAction}>
        <Button type="submit" className="w-full">
          Finish setup
        </Button>
      </form>
    </div>
  );
}
