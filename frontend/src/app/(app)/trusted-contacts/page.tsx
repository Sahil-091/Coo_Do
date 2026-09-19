import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { TrustedContactsClient } from "./TrustedContactsClient";
import type { TrustedContact, TrustedContactChannel, TrustedContactRelationship, TrustedContactScenario } from "./actions";

interface ApiTrustedContact { id: string; display_name: string; relationship: TrustedContactRelationship; channel: TrustedContactChannel; allowed_scenarios: TrustedContactScenario[]; created_at: string; }

function validScenario(value: string | undefined): TrustedContactScenario | undefined {
  return value === "feeling_overwhelmed" || value === "need_to_talk" || value === "practical_support" || value === "urgent_but_not_emergency" ? value : undefined;
}

export default async function TrustedContactsPage({ searchParams }: { searchParams: Promise<{ scenario?: string }> }) {
  const user = await requireOnboardedUser();
  const { scenario } = await searchParams;
  let contacts: TrustedContact[] = [];
  try {
    const rows = await internalApiFetch<ApiTrustedContact[]>(`/internal/users/${user.userId}/trusted-contacts`);
    contacts = rows.map((contact) => ({ id: contact.id, displayName: contact.display_name, relationship: contact.relationship, channel: contact.channel, allowedScenarios: contact.allowed_scenarios, createdAt: contact.created_at }));
  } catch {
    // Keep the form available during a temporary listing outage.
  }
  return <TrustedContactsClient initialContacts={contacts} initialScenario={validScenario(scenario)} />;
}
