import { EmptyState } from "@/components/EmptyState";
import { Shield } from "lucide-react";

export default function SafetyPage() {
  return (
    <EmptyState
      icon={Shield}
      title="Safety Center"
      description="Crisis resources, trusted contacts, and how we handle serious moments — built carefully, and reviewed before anything here goes live."
      phaseNote="Arrives in Phase 5 (crisis system) and Phase 10 (trusted contacts)"
    />
  );
}
