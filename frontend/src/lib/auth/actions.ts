"use server";

import { redirect } from "next/navigation";
import { flattenError } from "zod";
import { InternalApiError, internalApiFetch } from "@/lib/core-api-server";
import { requireAuthenticatedUser, requireOnboardedUser } from "./dal";
import { createSession, deleteSession } from "./session";
import {
  ageVerificationSchema,
  consentTypeSchema,
  displayNameSchema,
  loginSchema,
  registerSchema,
} from "./validation";

export interface ActionState {
  error?: string;
  fieldErrors?: Record<string, string[] | undefined>;
}

const GENERIC_ERROR: ActionState = {
  error: "Something went wrong. Please try again.",
};

export async function registerAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = registerSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) {
    return { fieldErrors: flattenError(parsed.error).fieldErrors };
  }

  let userId: string;
  try {
    const result = await internalApiFetch<{ user_id: string }>("/internal/auth/register", {
      method: "POST",
      body: JSON.stringify(parsed.data),
    });
    userId = result.user_id;
  } catch (err) {
    if (err instanceof InternalApiError && err.status === 409) {
      return { error: "An account with this email already exists." };
    }
    return GENERIC_ERROR;
  }

  await createSession(userId);
  redirect("/onboarding/age");
}

export async function loginAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const parsed = loginSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) {
    return { fieldErrors: flattenError(parsed.error).fieldErrors };
  }

  let userId: string;
  let ageVerified: boolean;
  try {
    const result = await internalApiFetch<{ user_id: string; age_verified: boolean }>(
      "/internal/auth/verify",
      { method: "POST", body: JSON.stringify(parsed.data) }
    );
    userId = result.user_id;
    ageVerified = result.age_verified;
  } catch (err) {
    if (err instanceof InternalApiError && err.status === 401) {
      return { error: "Incorrect email or password." };
    }
    return GENERIC_ERROR;
  }

  await createSession(userId);
  redirect(ageVerified ? "/" : "/onboarding/age");
}

export async function logoutAction(): Promise<void> {
  await deleteSession();
  redirect("/login");
}

export async function submitAgeAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState & { ageVerified?: boolean }> {
  const user = await requireAuthenticatedUser();

  const parsed = ageVerificationSchema.safeParse({
    dateOfBirth: formData.get("dateOfBirth"),
  });
  if (!parsed.success) {
    return { fieldErrors: flattenError(parsed.error).fieldErrors };
  }

  let ageVerified: boolean;
  try {
    const result = await internalApiFetch<{ age_verified: boolean }>(
      `/internal/users/${user.userId}/age-verification`,
      { method: "PUT", body: JSON.stringify({ date_of_birth: parsed.data.dateOfBirth }) }
    );
    ageVerified = result.age_verified;
  } catch {
    return GENERIC_ERROR;
  }

  if (ageVerified) {
    redirect("/onboarding/display-name");
  }
  // Under 18: do NOT redirect — the page shows a clear, kind message
  // and stops here. This is the hard gate actually holding.
  return { ageVerified: false };
}

export async function submitDisplayNameAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const user = await requireAuthenticatedUser();

  const parsed = displayNameSchema.safeParse({
    displayName: formData.get("displayName") || undefined,
  });
  if (!parsed.success) {
    return { fieldErrors: flattenError(parsed.error).fieldErrors };
  }

  try {
    await internalApiFetch(`/internal/users/${user.userId}/display-name`, {
      method: "PUT",
      body: JSON.stringify({ pseudonymous_display_name: parsed.data.displayName ?? null }),
    });
  } catch {
    return GENERIC_ERROR;
  }

  redirect("/onboarding/consent");
}

export async function completeOnboardingAction(): Promise<void> {
  // Consent step is entirely optional/skippable per R&D doc Section 11
  // — there is nothing to validate or persist here beyond letting the
  // student move on. Each individual consent toggle is already recorded
  // the moment it's flipped (see submitConsentAction), not batched here.
  await requireAuthenticatedUser();
  redirect("/");
}

export async function submitConsentAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const user = await requireAuthenticatedUser();

  const consentType = consentTypeSchema.safeParse(formData.get("consentType"));
  const granted = formData.get("granted") === "true";
  if (!consentType.success) {
    return GENERIC_ERROR;
  }

  try {
    await internalApiFetch(`/internal/users/${user.userId}/consents`, {
      method: "POST",
      body: JSON.stringify({ consent_type: consentType.data, granted }),
    });
  } catch {
    return GENERIC_ERROR;
  }

  return {};
}

export async function updatePrivacySettingsAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const user = await requireOnboardedUser();

  try {
    await internalApiFetch(`/internal/users/${user.userId}/privacy-settings`, {
      method: "PUT",
      body: JSON.stringify({
        profile_visible_in_matching: formData.get("profileVisibleInMatching") === "true",
        display_name_visible_in_rooms: formData.get("displayNameVisibleInRooms") === "true",
      }),
    });
  } catch {
    return GENERIC_ERROR;
  }

  return {};
}

export async function requestDataAction(
  _prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  const user = await requireOnboardedUser();
  const requestType = formData.get("requestType");
  if (requestType !== "export" && requestType !== "deletion") {
    return GENERIC_ERROR;
  }

  try {
    await internalApiFetch(`/internal/users/${user.userId}/data-requests`, {
      method: "POST",
      body: JSON.stringify({ request_type: requestType }),
    });
  } catch {
    return GENERIC_ERROR;
  }

  return {};
}
