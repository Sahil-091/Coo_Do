import { EmptyState } from "@/components/EmptyState";
import { BookOpen } from "lucide-react";

export default function JournalPage() {
  return (
    <EmptyState
      icon={BookOpen}
      title="What's changing, in your own words"
      description="A private, narrative record — not a score. Come back in a week or a month and see what's actually different."
      phaseNote="Arrives in Phase 8"
    />
  );
}
