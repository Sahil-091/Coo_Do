import { Button } from "@/components/ui/Button";
import { ConsentToggle } from "@/components/ConsentToggle";
import { CONSENT_ITEMS } from "@/lib/consent-config";
import { logoutAction } from "@/lib/auth/actions";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import Link from "next/link";
import { DataRequestSection } from "./DataRequestSection";
import { PrivacyToggles } from "./PrivacyToggles";

interface ConsentStateResponse {
  consent_type: string;
  granted: boolean;
  updated_at: string | null;
}

interface PrivacySettingsResponse {
  profile_visible_in_matching: boolean;
  display_name_visible_in_rooms: boolean;
  updated_at: string;
}

interface DataRequestResponse {
  id: string;
  request_type: "export" | "deletion";
  status: "pending" | "completed" | "denied";
  created_at: string;
  completed_at: string | null;
  notes: string | null;
}

export default async function SettingsPage() {
  const user = await requireOnboardedUser();

  const [consents, privacySettings, dataRequests] = await Promise.all([
    internalApiFetch<ConsentStateResponse[]>(`/internal/users/${user.userId}/consents`),
    internalApiFetch<PrivacySettingsResponse>(`/internal/users/${user.userId}/privacy-settings`),
    internalApiFetch<DataRequestResponse[]>(`/internal/users/${user.userId}/data-requests`),
  ]);

  const grantedByType = Object.fromEntries(consents.map((c) => [c.consent_type, c.granted]));

  return (
    <div className="flex max-w-lg flex-col gap-8 pb-8">
      <div>
        <h1 className="font-display text-2xl text-ink">
          Your account, your data, your choices
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Separate, specific controls — nothing bundled into one big &ldquo;I agree.&rdquo;
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Account</h2>
        <div className="rounded-lg border border-border-subtle bg-paper-raised p-4">
          <div className="flex flex-col gap-1">
            <span className="text-xs text-ink-muted">Email</span>
            <span className="text-sm text-ink">{user.email}</span>
          </div>
          {user.pseudonymousDisplayName && (
            <div className="mt-3 flex flex-col gap-1">
              <span className="text-xs text-ink-muted">Display name</span>
              <span className="text-sm text-ink">{user.pseudonymousDisplayName}</span>
            </div>
          )}
        </div>
        <form action={logoutAction}>
          <Button type="submit" variant="secondary">
            Log out
          </Button>
        </form>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">What you&rsquo;ve opted into</h2>
        <p className="text-sm text-ink-muted">
          Nothing here affects your ability to use check-ins or tiny actions.
        </p>
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
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Visibility</h2>
        <PrivacyToggles
          initialProfileVisibleInMatching={privacySettings.profile_visible_in_matching}
          initialDisplayNameVisibleInRooms={privacySettings.display_name_visible_in_rooms}
        />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Find someone like me</h2>
        <p className="text-sm text-ink-muted">Use shared interests and activity styles to find low-pressure, non-dating common ground.</p>
        <Link className="text-sm font-semibold text-lamp underline" href="/matching">Set up matching</Link>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Trusted people</h2>
        <p className="text-sm text-ink-muted">Save people you may choose to reach out to. Their details are encrypted, and Coo_Do never contacts them automatically.</p>
        <Link className="text-sm font-semibold text-lamp underline" href="/trusted-contacts">Manage trusted people</Link>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Your data</h2>
        <DataRequestSection initialRequests={dataRequests} />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="font-display text-lg text-ink">Your journal</h2>
        <p className="text-sm text-ink-muted">Journal requests are recorded separately so they can be handled without affecting the rest of your account. You can also <Link className="font-semibold text-lamp underline" href="/journal">export or permanently delete journal entries now</Link>.</p>
        <DataRequestSection initialRequests={dataRequests.filter((request) => request.notes === "journal")} scope="journal" />
      </section>
    </div>
  );
}
