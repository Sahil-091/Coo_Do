import { EmptyState } from "@/components/EmptyState";
import { Users } from "lucide-react";

export default function CommunityPage() {
  return (
    <EmptyState
      icon={Users}
      title="Shared rooms, shared activities"
      description="Study sessions, situation-based rooms, and low-pressure ways to be around people — moderated, and never about being alone with strangers unsupervised."
      phaseNote="Arrives in Phase 9 (activities) and Phase 12 (rooms, once moderation is live)"
    />
  );
}
