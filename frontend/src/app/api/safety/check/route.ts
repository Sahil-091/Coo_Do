import { NextResponse } from "next/server";
import { getSessionPayload } from "@/lib/auth/session";
import { internalSafetyFetch } from "@/lib/safety-server";

const SOURCES = new Set(["checkin_freetext", "ai_navigator", "community_post", "journal"]);

export async function POST(request: Request) {
  const session = await getSessionPayload();
  if (!session?.userId) return NextResponse.json({ error: "Sign in is required." }, { status: 401 });
  try {
    const body: unknown = await request.json();
    if (!body || typeof body !== "object") throw new Error("Invalid request");
    const { text, source } = body as { text?: unknown; source?: unknown };
    if (typeof text !== "string" || !text.trim() || text.length > 5000 || typeof source !== "string" || !SOURCES.has(source)) {
      return NextResponse.json({ error: "Invalid safety-check request." }, { status: 400 });
    }
    const result = await internalSafetyFetch("/v1/check-text", { method: "POST", body: JSON.stringify({ text, source, user_ref: session.userId }) });
    return NextResponse.json(result);
  } catch {
    // Fail closed: downstream callers must not store or forward unchecked text.
    return NextResponse.json({ error: "Safety screening is unavailable.", degraded: true }, { status: 503 });
  }
}
