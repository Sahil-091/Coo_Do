import "server-only";
import { serverEnv } from "@/lib/env.server";

export class InternalApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "InternalApiError";
  }
}

/**
 * Calls core-api's /internal/* routes — server-side only, with the
 * shared secret header. Never import this from a Client Component (the
 * `server-only` guard above turns that into a build error, not a
 * runtime surprise). The browser never talks to core-api directly.
 */
export async function internalApiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${serverEnv.CORE_API_INTERNAL_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Secret": serverEnv.INTERNAL_SHARED_SECRET,
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = undefined;
    }
    throw new InternalApiError(`core-api request to ${path} failed`, res.status, body);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}
