"use client";

import { Footprints, LifeBuoy, Users } from "lucide-react";
import Link from "next/link";
import { useActionState, useState, useTransition } from "react";
import { Button } from "@/components/ui/Button";
import { ChipOption } from "@/components/ui/ChipOption";
import { submitCheckInAction, type CheckInActionState } from "@/lib/checkin/actions";
import { getTimeOfDay } from "@/lib/checkin/time-of-day";
import {
  FEELINGS,
  FEELING_LABELS,
  NEEDS,
  NEED_LABELS,
  PATH_DESTINATIONS,
  type Feeling,
  type Need,
  type SuggestedPath,
} from "@/lib/checkin/types";

type Step = "feelings" | "need" | "result";

const PATH_ICON: Record<SuggestedPath, typeof Footprints> = {
  tiny_action: Footprints,
  presence_mode: Users,
  professional_help: LifeBuoy,
};

const PATH_HEADLINE: Record<SuggestedPath, string> = {
  tiny_action: "One small step might help",
  presence_mode: "Let's find people nearby",
  professional_help: "Let's get you real support",
};

const initialState: CheckInActionState = {};

export function CheckInFlow() {
  const [step, setStep] = useState<Step>("feelings");
  const [selectedFeelings, setSelectedFeelings] = useState<Feeling[]>([]);
  const [selectedNeed, setSelectedNeed] = useState<Need | null>(null);
  const [state, formAction, isPending] = useActionState(submitCheckInAction, initialState);
  const [, startTransition] = useTransition();
  const [visible, setVisible] = useState(true);

  function goToStep(next: Step) {
    setStep(next);
    setVisible(false);
    requestAnimationFrame(() => setVisible(true));
  }

  function toggleFeeling(value: string) {
    const feeling = value as Feeling;
    setSelectedFeelings((prev) =>
      prev.includes(feeling) ? prev.filter((f) => f !== feeling) : [...prev, feeling]
    );
  }

  function handleSubmit() {
    if (!selectedNeed) return;
    const formData = new FormData();
    for (const feeling of selectedFeelings) formData.append("feelings", feeling);
    formData.set("statedNeed", selectedNeed);
    // Computed HERE, client-side, from the student's own clock — see
    // actions.ts's doc comment for why this can't happen server-side.
    formData.set("timeOfDay", getTimeOfDay(new Date()));

    startTransition(() => {
      formAction(formData);
    });
    goToStep("result");
  }

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6">
      {step !== "result" && <StepIndicator current={step} />}

      <div className={"transition-opacity duration-150 " + (visible ? "opacity-100" : "opacity-0")}>
        {step === "feelings" && (
          <FeelingsStep
            selected={selectedFeelings}
            onToggle={toggleFeeling}
            onContinue={() => goToStep("need")}
          />
        )}

        {step === "need" && (
          <NeedStep
            selected={selectedNeed}
            onSelect={(value) => setSelectedNeed(value as Need)}
            onBack={() => goToStep("feelings")}
            onSubmit={handleSubmit}
            isPending={isPending}
          />
        )}

        {step === "result" && (
          <ResultStep
            isPending={isPending}
            state={state}
            onStartOver={() => {
              setSelectedFeelings([]);
              setSelectedNeed(null);
              goToStep("feelings");
            }}
          />
        )}
      </div>
    </div>
  );
}

function StepIndicator({ current }: { current: "feelings" | "need" }) {
  const steps: { key: "feelings" | "need"; label: string }[] = [
    { key: "feelings", label: "How you feel" },
    { key: "need", label: "What you need" },
  ];
  return (
    <div className="flex items-center gap-2" aria-hidden="true">
      {steps.map((s) => (
        <span
          key={s.key}
          className={
            "h-1.5 flex-1 rounded-full transition-colors " +
            (s.key === current ? "bg-lamp" : "bg-border-subtle")
          }
        />
      ))}
    </div>
  );
}

function FeelingsStep({
  selected,
  onToggle,
  onContinue,
}: {
  selected: Feeling[];
  onToggle: (value: string) => void;
  onContinue: () => void;
}) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display text-2xl text-ink">How are you, really?</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Pick everything that fits — there&rsquo;s no wrong answer.
        </p>
      </div>

      <div role="group" aria-label="How are you feeling" className="flex flex-wrap gap-2">
        {FEELINGS.map((feeling) => (
          <ChipOption
            key={feeling}
            type="checkbox"
            name="feelings"
            value={feeling}
            checked={selected.includes(feeling)}
            onChange={onToggle}
          >
            {FEELING_LABELS[feeling]}
          </ChipOption>
        ))}
      </div>

      <Button type="button" disabled={selected.length === 0} onClick={onContinue} className="mt-2">
        Continue
      </Button>
    </div>
  );
}

function NeedStep({
  selected,
  onSelect,
  onBack,
  onSubmit,
  isPending,
}: {
  selected: Need | null;
  onSelect: (value: string) => void;
  onBack: () => void;
  onSubmit: () => void;
  isPending: boolean;
}) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="font-display text-2xl text-ink">What do you need right now?</h1>
        <p className="mt-1 text-sm text-ink-muted">Just pick the closest one.</p>
      </div>

      <div role="radiogroup" aria-label="What do you need right now" className="flex flex-wrap gap-2">
        {NEEDS.map((need) => (
          <ChipOption
            key={need}
            type="radio"
            name="statedNeed"
            value={need}
            checked={selected === need}
            onChange={onSelect}
          >
            {NEED_LABELS[need]}
          </ChipOption>
        ))}
      </div>

      <div className="mt-2 flex items-center gap-3">
        <Button type="button" variant="ghost" onClick={onBack} disabled={isPending}>
          Back
        </Button>
        <Button type="button" disabled={!selected || isPending} onClick={onSubmit} className="flex-1">
          {isPending ? "One sec…" : "See what might help"}
        </Button>
      </div>
    </div>
  );
}

function ResultStep({
  state,
  isPending,
  onStartOver,
}: {
  state: CheckInActionState;
  isPending: boolean;
  onStartOver: () => void;
}) {
  if (isPending || (!state.result && !state.error)) {
    return (
      <div className="flex flex-col items-center gap-3 py-12 text-center">
        <div className="h-10 w-10 animate-pulse rounded-full bg-lamp-tint" aria-hidden="true" />
        <p className="text-sm text-ink-muted">Finding something that fits…</p>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="flex flex-col gap-4">
        <p role="alert" className="text-sm text-clay">
          {state.error}
        </p>
        <Button type="button" variant="secondary" onClick={onStartOver}>
          Try again
        </Button>
      </div>
    );
  }

  if (!state.result) {
    // Shouldn't be reachable (the pending/error branches above cover
    // every other case), but fail visibly rather than crash on a
    // non-null assertion if some future edit changes that invariant.
    return null;
  }

  const { path, reason, checkinId } = state.result;
  const Icon = PATH_ICON[path];
  const destination = PATH_DESTINATIONS[path];
  // Only Tiny Action currently ties attempts back to the check-in that
  // triggered them (action_attempts.related_checkin_id) — Presence Mode
  // and Professional Help don't have an equivalent attempt-tracking
  // concept yet, so there's nothing to pass through for those.
  const destinationHref =
    path === "tiny_action" ? `${destination.href}?checkinId=${checkinId}` : destination.href;

  return (
    <div className="flex flex-col items-start gap-4 py-2">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-lamp-tint">
        <Icon className="h-6 w-6 text-lamp" aria-hidden="true" />
      </span>
      <div>
        <h1 className="font-display text-2xl text-ink">{PATH_HEADLINE[path]}</h1>
        <p className="mt-2 text-sm text-ink-muted">{reason}</p>
      </div>

      <div className="mt-2 flex w-full flex-col gap-2 sm:flex-row">
        <Link href={destinationHref} className="flex-1">
          <Button type="button" className="w-full">
            {destination.cta}
          </Button>
        </Link>
        <Button type="button" variant="ghost" onClick={onStartOver}>
          Check in again
        </Button>
      </div>

      <Link href="/" className="text-sm text-ink-muted underline underline-offset-2">
        Not now — back to Home
      </Link>
    </div>
  );
}
