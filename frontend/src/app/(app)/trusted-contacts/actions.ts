"use server";

import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";

export type TrustedContactRelationship = "friend" | "parent" | "sibling" | "teacher" | "counselor" | "mentor" | "other";
export type TrustedContactScenario = "feeling_overwhelmed" | "need_to_talk" | "practical_support" | "urgent_but_not_emergency";
export type TrustedContactChannel = "sms" | "email";

export interface TrustedContact {
  id: string;
  displayName: string;
  relationship: TrustedContactRelationship;
  channel: TrustedContactChannel;
  allowedScenarios: TrustedContactScenario[];
  createdAt: string;
}

interface ApiTrustedContact {
  id: string;
  display_name: string;
  relationship: TrustedContactRelationship;
  channel: TrustedContactChannel;
  allowed_scenarios: TrustedContactScenario[];
  created_at: string;
}

function mapContact(contact: ApiTrustedContact): TrustedContact {
  return { id: contact.id, displayName: contact.display_name, relationship: contact.relationship, channel: contact.channel, allowedScenarios: contact.allowed_scenarios, createdAt: contact.created_at };
}

export async function createTrustedContactAction(payload: {
  displayName: string;
  relationship: TrustedContactRelationship;
  channel: TrustedContactChannel;
  contactValue: string;
  allowedScenarios: TrustedContactScenario[];
}): Promise<TrustedContact | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const contact = await internalApiFetch<ApiTrustedContact>(`/internal/users/${user.userId}/trusted-contacts`, {
      method: "POST",
      body: JSON.stringify({ display_name: payload.displayName, relationship: payload.relationship, channel: payload.channel, contact_value: payload.contactValue, allowed_scenarios: payload.allowedScenarios }),
    });
    return mapContact(contact);
  } catch {
    return { error: "Couldn’t save this contact. Please check the details and try again." };
  }
}

export async function deleteTrustedContactAction(contactId: string): Promise<{ error?: string }> {
  const user = await requireOnboardedUser();
  try {
    await internalApiFetch<void>(`/internal/users/${user.userId}/trusted-contacts/${contactId}`, { method: "DELETE" });
    return {};
  } catch {
    return { error: "Couldn’t remove this contact. Please try again." };
  }
}

export async function prepareTrustedOutreachAction(contactId: string, scenario: TrustedContactScenario): Promise<{ destination: string; contactName: string } | { error: string }> {
  const user = await requireOnboardedUser();
  try {
    const result = await internalApiFetch<{ destination: string; contact_name: string }>(`/internal/users/${user.userId}/trusted-contacts/${contactId}/outreach`, { method: "POST", body: JSON.stringify({ scenario }) });
    return { destination: result.destination, contactName: result.contact_name };
  } catch {
    return { error: "Couldn’t prepare that message. Nothing was sent." };
  }
}
