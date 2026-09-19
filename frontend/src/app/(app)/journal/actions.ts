"use server";
import { revalidatePath } from "next/cache";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";

export interface JournalExportEntry {
  id: string;
  body: string;
  created_at: string;
  updated_at: string;
}

type JournalActionState = { error?: string };

export async function createJournalEntryAction(_: { error?: string }, formData: FormData): Promise<{ error?: string }> {
  const body = String(formData.get("body") ?? "").trim();
  if (!body) return { error: "Write something before saving." };
  const user = await requireOnboardedUser();
  try { await internalApiFetch(`/internal/users/${user.userId}/journal`, { method: "POST", body: JSON.stringify({ body }) }); } catch { return { error: "Your reflection could not be saved. Please try again." }; }
  revalidatePath("/journal"); return {};
}

/** Download data is returned only to the authenticated user's browser. */
export async function exportJournalAction(): Promise<{ entries?: JournalExportEntry[]; error?: string }> {
  const user = await requireOnboardedUser();
  try {
    const result = await internalApiFetch<{ entries: JournalExportEntry[] }>(`/internal/users/${user.userId}/journal/export`);
    return { entries: result.entries };
  } catch {
    return { error: "Your journal export is temporarily unavailable. Please try again." };
  }
}

export async function deleteJournalEntryAction(_: JournalActionState, formData: FormData): Promise<JournalActionState> {
  const entryId = String(formData.get("entryId") ?? "");
  if (!entryId) return { error: "That reflection could not be identified." };
  const user = await requireOnboardedUser();
  try {
    await internalApiFetch(`/internal/users/${user.userId}/journal/${entryId}`, { method: "DELETE" });
  } catch {
    return { error: "That reflection could not be deleted. Please try again." };
  }
  revalidatePath("/journal");
  return {};
}

export async function deleteAllJournalEntriesAction(_: JournalActionState): Promise<JournalActionState> {
  const user = await requireOnboardedUser();
  try {
    await internalApiFetch(`/internal/users/${user.userId}/journal`, { method: "DELETE" });
  } catch {
    return { error: "Your journal could not be deleted. Please try again." };
  }
  revalidatePath("/journal");
  return {};
}
