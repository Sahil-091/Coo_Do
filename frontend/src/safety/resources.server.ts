import "server-only";

import { serverEnv } from "@/lib/env.server";

export interface CrisisResource { name: string; phone: string; phone_uri: string; description: string }
export interface CrisisResources { region: string; emergency_note: string; resources: CrisisResource[] }

export async function getCrisisResources(): Promise<CrisisResources | null> {
  try {
    const response = await fetch(`${serverEnv.SAFETY_SERVICE_INTERNAL_URL}/v1/resources`, { cache: "no-store" });
    if (!response.ok) return null;
    return response.json() as Promise<CrisisResources>;
  } catch {
    return null;
  }
}
