/**
 * Thin fetch wrapper for talking to core-api. Feature modules should go
 * through this rather than calling `fetch` directly, so auth headers,
 * error handling, and base URL live in exactly one place.
 *
 * No feature is wired to this yet (Phase 0 = infrastructure only).
 */
import { env } from "./env";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${env.NEXT_PUBLIC_CORE_API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = undefined;
    }
    throw new ApiError(`Request to ${path} failed`, res.status, body);
  }

  return res.json() as Promise<T>;
}
