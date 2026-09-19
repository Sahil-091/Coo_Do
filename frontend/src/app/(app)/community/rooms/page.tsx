import { requireOnboardedUser } from "@/lib/auth/dal";
import { internalModerationApiFetch } from "@/lib/moderation-api-server";
import { getCrisisResources } from "@/safety/resources.server";
import { SituationRoomsClient } from "./SituationRoomsClient";
import { mapRoom, type SituationRoom } from "./types";

export default async function SituationRoomsPage() {
  await requireOnboardedUser();
  const [roomsResult, resources] = await Promise.all([
    internalModerationApiFetch<unknown[]>("/internal/community/rooms").catch(() => []),
    getCrisisResources(),
  ]);
  const rooms: SituationRoom[] = roomsResult.map((room) => mapRoom(room as Parameters<typeof mapRoom>[0]));
  return <SituationRoomsClient initialRooms={rooms} crisisResources={resources} />;
}
