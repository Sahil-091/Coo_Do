import "server-only";

import { serverEnv } from "@/lib/env.server";

/** Server-only boundary: the browser never receives the matching service secret. */
export async function internalMatchingApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${serverEnv.MATCHING_SERVICE_INTERNAL_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Secret": serverEnv.INTERNAL_SHARED_SECRET,
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`matching-service request to ${path} failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
