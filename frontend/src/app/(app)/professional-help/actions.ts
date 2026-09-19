"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalApiFetch } from "@/lib/core-api-server";
import { serverEnv } from "@/lib/env.server";

function isAllowedEditor(email: string): boolean {
  return serverEnv.PROFESSIONAL_HELP_EDITOR_EMAILS?.split(",")
    .map((entry) => entry.trim().toLowerCase())
    .includes(email.toLowerCase()) ?? false;
}

function optional(value: FormDataEntryValue | null): string | null {
  const text = typeof value === "string" ? value.trim() : "";
  return text || null;
}

function lines(value: FormDataEntryValue | null): string[] {
  return typeof value === "string" ? value.split("\n").map((line) => line.trim()).filter(Boolean) : [];
}

/** Re-check authorization here; hiding the editor page is not a boundary. */
export async function saveProfessionalResourceAction(formData: FormData): Promise<void> {
  const editor = await requireOnboardedUser();
  if (!isAllowedEditor(editor.email)) throw new Error("Not authorized to edit professional-help resources.");
  const resourceId = optional(formData.get("resourceId"));
  const payload = {
    resource_key: String(formData.get("resourceKey") ?? "").trim(), region: String(formData.get("region") ?? "").trim(),
    category: String(formData.get("category") ?? "").trim(), title: String(formData.get("title") ?? "").trim(),
    summary: String(formData.get("summary") ?? "").trim(), contact_label: optional(formData.get("contactLabel")),
    contact_value: optional(formData.get("contactValue")), contact_uri: optional(formData.get("contactUri")),
    booking_steps: lines(formData.get("bookingSteps")), what_to_expect: optional(formData.get("whatToExpect")),
    opening_lines: lines(formData.get("openingLines")), last_verified_at: optional(formData.get("lastVerifiedAt")),
  };
  await internalApiFetch(resourceId ? `/internal/professional-resources/${resourceId}` : "/internal/professional-resources", {
    method: resourceId ? "PUT" : "POST", body: JSON.stringify(payload),
  });
  revalidatePath("/professional-help");
  revalidatePath("/professional-help/editor");
}

/**
 * This is deliberately a server action rather than a browser-to-core-api
 * call: it retains the internal-service secret boundary and ties the explicit
 * open/call event to the currently signed-in student.
 */
export async function openProfessionalResourceAction(formData: FormData): Promise<void> {
  const user = await requireOnboardedUser();
  const resourceId = String(formData.get("resourceId") ?? "");
  if (!resourceId) throw new Error("Professional resource was not specified.");
  const result = await internalApiFetch<{ destination: string }>(
    `/internal/users/${user.userId}/professional-resources/${resourceId}/open`,
    { method: "POST" },
  );
  redirect(result.destination);
}
