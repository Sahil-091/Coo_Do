import { EmptyState } from "@/components/EmptyState";
import { LifeBuoy } from "lucide-react";

export default function ProfessionalHelpPage() {
  return (
    <EmptyState
      icon={LifeBuoy}
      title="Real support, without the guesswork"
      description="What counseling actually looks like, how to book a first session, and what to say — reachable from here anytime, no check-in required first."
      phaseNote="Arrives in Phase 7"
    />
  );
}
