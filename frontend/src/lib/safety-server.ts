import "server-only";

import { serverEnv } from "@/lib/env.server";

export async function internalSafetyFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${serverEnv.SAFETY_SERVICE_INTERNAL_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Internal-Secret": serverEnv.INTERNAL_SHARED_SECRET, ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Safety service request failed: ${response.status}`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function reviewerSafetyFetch<T>(path: string, init?: RequestInit): Promise<T> {
  if (!serverEnv.SAFETY_REVIEWER_TOKEN) throw new Error("Safety reviewer access is not configured");
  const response = await fetch(`${serverEnv.SAFETY_SERVICE_INTERNAL_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Safety-Reviewer-Token": serverEnv.SAFETY_REVIEWER_TOKEN, ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Safety reviewer request failed: ${response.status}`);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
