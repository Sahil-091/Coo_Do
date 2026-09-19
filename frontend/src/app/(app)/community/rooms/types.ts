export type SituationTopic = "feeling_lonely" | "exam_anxiety" | "homesick" | "need_someone_to_talk_to";
export type CommunityReportCategory = "harassment" | "sexual_content" | "spam_or_scam" | "self_harm_concern" | "other";

export interface SituationRoom { id: string; topic: SituationTopic; createdAt: string; }
export interface CommunityPost { id: string; body: string; createdAt: string; }

interface ApiRoom { id: string; topic: SituationTopic; created_at: string; }
interface ApiPost { id: string; body: string; created_at: string; }

export function mapRoom(room: ApiRoom): SituationRoom { return { id: room.id, topic: room.topic, createdAt: room.created_at }; }
export function mapPost(post: ApiPost): CommunityPost { return { id: post.id, body: post.body, createdAt: post.created_at }; }
