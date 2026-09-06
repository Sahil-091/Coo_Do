"use client";

import { LifeBuoy } from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { getSuggestionAction, logAttemptAction } from "@/lib/tiny-action/actions";
import type { TinyActionRung } from "@/lib/tiny-action/types";

type ViewState =
  | { kind: "ladder" }
  | { kind: "completed" }
  | { kind: "skipped" }
  | { kind: "floor_acknowledged"; showSupportNudge: boolean };

function defaultRungIndex(ladder: TinyActionRung[]): number {
  const middle = ladder.findIndex((r) => r.difficultyLevel === 2);
  return middle >= 0 ? middle : Math.floor(ladder.length / 2);
}

export function TinyActionFlow({
  initialLadder,
  checkinId,
}: {
  initialLadder: TinyActionRung[];
  checkinId?: string;
}) {
  const [ladder, setLadder] = useState(initialLadder);
  const [rungIndex, setRungIndex] = useState(() => defaultRungIndex(initialLadder));
  const [view, setView] = useState<ViewState>({ kind: "ladder" });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const current = ladder[rungIndex];
  const atFloor = rungIndex === 0;
  const atCeiling = rungIndex === ladder.length - 1;

  function handleBigger() {
    setRungIndex((i) => Math.min(i + 1, ladder.length - 1));
  }

  function handleSmaller() {
    setErrorMessage(null);
    startTransition(async () => {
      const result = await logAttemptAction(current.id, "reduced", checkinId);
      if ("error" in result) {
        setErrorMessage(result.error);
        return;
      }
      if (atFloor) {
        // This IS "I couldn't do it, even this" — the required safety
        // check (R&D doc Section 5.3) lives entirely server-side; here
        // we just render whatever it decided.
        setView({ kind: "floor_acknowledged", showSupportNudge: result.showSupportNudge });
      } else {
        setRungIndex((i) => i - 1);
      }
    });
  }

  function handleComplete() {
    setErrorMessage(null);
    startTransition(async () => {
      const result = await logAttemptAction(current.id, "completed", checkinId);
      if ("error" in result) {
        setErrorMessage(result.error);
        return;
      }
      setView({ kind: "completed" });
    });
  }

  function handleSkip() {
    setErrorMessage(null);
    startTransition(async () => {
      const result = await logAttemptAction(current.id, "skipped", checkinId);
      if ("error" in result) {
        setErrorMessage(result.error);
        return;
      }
      setView({ kind: "skipped" });
    });
  }

  function handleTryAnother() {
    setErrorMessage(null);
    startTransition(async () => {
      const result = await getSuggestionAction();
      if ("error" in result) {
        setErrorMessage(result.error);
        return;
      }
      setLadder(result.ladder);
      setRungIndex(defaultRungIndex(result.ladder));
      setView({ kind: "ladder" });
    });
  }

  if (view.kind === "completed") {
    return <CompletedView onTryAnother={handleTryAnother} isPending={isPending} />;
  }
  if (view.kind === "skipped") {
    return <SkippedView onTryAnother={handleTryAnother} isPending={isPending} />;
  }
  if (view.kind === "floor_acknowledged") {
    return (
      <FloorAcknowledgedView
        showSupportNudge={view.showSupportNudge}
        onTryAnother={handleTryAnother}
        isPending={isPending}
      />
    );
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl text-ink">{current.title}</h1>
        <p className="mt-2 text-sm text-ink-muted">{current.description}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {!atCeiling && (
          <Button type="button" variant="secondary" size="sm" onClick={handleBigger} disabled={isPending}>
            Make it bigger
          </Button>
        )}
        {!atFloor && (
          <Button type="button" variant="secondary" size="sm" onClick={handleSmaller} disabled={isPending}>
            Make it smaller
          </Button>
        )}
        {atFloor && (
          <Button type="button" variant="secondary" size="sm" onClick={handleSmaller} disabled={isPending}>
            Even this feels like too much right now
          </Button>
        )}
      </div>

      {errorMessage && (
        <p role="alert" className="text-sm text-clay">
          {errorMessage}
        </p>
      )}

      <div className="flex gap-3">
        <Button type="button" onClick={handleComplete} disabled={isPending} className="flex-1">
          I did it
        </Button>
        <Button type="button" variant="ghost" onClick={handleSkip} disabled={isPending}>
          Not right now
        </Button>
      </div>
    </div>
  );
}

function CompletedView({ onTryAnother, isPending }: { onTryAnother: () => void; isPending: boolean }) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-start gap-4 py-4">
      <div>
        <h1 className="font-display text-2xl text-ink">You did that. That counts.</h1>
        <p className="mt-2 text-sm text-ink-muted">
          No streak to keep up, no score — just one real thing you actually did.
        </p>
      </div>
      <div className="flex gap-2">
        <Button type="button" variant="secondary" onClick={onTryAnother} disabled={isPending}>
          See another
        </Button>
        <Link href="/">
          <Button type="button" variant="ghost">
            Back to Home
          </Button>
        </Link>
      </div>
    </div>
  );
}

function SkippedView({ onTryAnother, isPending }: { onTryAnother: () => void; isPending: boolean }) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-start gap-4 py-4">
      <div>
        <h1 className="font-display text-2xl text-ink">That&rsquo;s okay</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Not every moment is the right one. Nothing here is tracking that against you.
        </p>
      </div>
      <div className="flex gap-2">
        <Button type="button" variant="secondary" onClick={onTryAnother} disabled={isPending}>
          See another
        </Button>
        <Link href="/">
          <Button type="button" variant="ghost">
            Back to Home
          </Button>
        </Link>
      </div>
    </div>
  );
}

function FloorAcknowledgedView({
  showSupportNudge,
  onTryAnother,
  isPending,
}: {
  showSupportNudge: boolean;
  onTryAnother: () => void;
  isPending: boolean;
}) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-start gap-4 py-4">
      <div>
        <h1 className="font-display text-2xl text-ink">That&rsquo;s real information, not a failure</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Thanks for being honest about where you&rsquo;re at. Even naming that something
          feels like too much right now matters.
        </p>
      </div>

      {showSupportNudge && (
        <div className="flex w-full flex-col gap-3 rounded-lg border border-lamp bg-lamp-tint p-4">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-paper-raised">
              <LifeBuoy className="h-5 w-5 text-lamp" aria-hidden="true" />
            </span>
            <p className="text-sm text-ink">
              It looks like even the smallest steps have felt like a lot lately. That&rsquo;s
              worth paying attention to — here&rsquo;s a low-pressure way to get some real
              support, whenever you&rsquo;re ready. Crisis resources are also always
              available from the Safety Center link at the bottom of the screen.
            </p>
          </div>
          <Link href="/professional-help">
            <Button type="button" className="w-full sm:w-auto">
              See how to get support
            </Button>
          </Link>
        </div>
      )}

      <div className="flex gap-2">
        <Button type="button" variant="secondary" onClick={onTryAnother} disabled={isPending}>
          Try something else
        </Button>
        <Link href="/">
          <Button type="button" variant="ghost">
            Back to Home
          </Button>
        </Link>
      </div>
    </div>
  );
}
