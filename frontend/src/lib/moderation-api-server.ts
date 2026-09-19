import "server-only";

import { serverEnv } from "@/lib/env.server";

/** Server-only gateway; anonymous-room APIs are never called from a browser directly. */
export async function internalModerationApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${serverEnv.MODERATION_SERVICE_INTERNAL_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Internal-Secret": serverEnv.INTERNAL_SHARED_SECRET, ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`moderation-service request to ${path} failed (${response.status})`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/**
 * Deliberately separate from the general internal gateway. Only the limited
 * reviewer role gets this credential, and it is never exposed to a browser.
 */
export async function reviewerModerationApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!serverEnv.MODERATION_REVIEWER_TOKEN) {
    throw new Error("Moderation reviewer access is not configured");
  }
  const response = await fetch(`${serverEnv.MODERATION_SERVICE_INTERNAL_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Moderation-Reviewer-Token": serverEnv.MODERATION_REVIEWER_TOKEN,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`moderation reviewer request to ${path} failed (${response.status})`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
