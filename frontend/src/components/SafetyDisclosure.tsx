import { Info } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/cn";

/**
 * The persistent disclosure convention every AI-facing screen (Phase 6
 * onward) should reuse — see R&D doc Section 10. Deliberately quiet:
 * this is not a legal-disclaimer footer shouting for attention, it's a
 * calm, always-there affordance that also happens to be a fast path to
 * Safety Center — see DESIGN.md's layout rationale for why that
 * double-duty matters (Professional Help / Safety Center stay one tap
 * away without needing a dedicated bottom-tab slot each).
 */
export function SafetyDisclosure({ className }: { className?: string }) {
  return (
    <Link
      href="/safety"
      className={cn(
        "flex items-center gap-2 rounded-md border border-border-subtle bg-paper px-3 py-2.5 text-xs text-ink-muted transition-colors hover:bg-paper-raised hover:text-ink",
        className
      )}
    >
      <Info className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span>
        This is a support companion, not a therapist.{" "}
        <span className="font-medium text-ink">See support options ›</span>
      </span>
    </Link>
  );
}
