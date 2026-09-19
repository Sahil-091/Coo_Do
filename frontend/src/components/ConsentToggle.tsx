"use client";

import { useState, useTransition } from "react";
import { submitConsentAction } from "@/lib/auth/actions";
import type { ConsentType } from "@/lib/auth/validation";
import { ToggleRow } from "@/components/ui/ToggleRow";

interface ConsentToggleProps {
  consentType: ConsentType;
  title: string;
  description: string;
  initialGranted: boolean;
}

/**
 * Each toggle saves itself immediately on flip — no separate "Save"
 * button, no bundled "I agree to everything". Each is its own
 * consent_records row (R&D doc Section 11: "granular, separately-
 * toggleable"). Optimistic UI with revert-on-failure.
 */
export function ConsentToggle({
  consentType,
  title,
  description,
  initialGranted,
}: ConsentToggleProps) {
  const [granted, setGranted] = useState(initialGranted);
  const [failed, setFailed] = useState(false);
  const [isPending, startTransition] = useTransition();

  function handleToggle() {
    const next = !granted;
    setGranted(next);
    setFailed(false);

    startTransition(async () => {
      const formData = new FormData();
      formData.set("consentType", consentType);
      formData.set("granted", String(next));
      const result = await submitConsentAction({}, formData);
      if (result.error) {
        setGranted(!next); // revert
        setFailed(true);
      }
    });
  }

  return (
    <ToggleRow
      title={title}
      description={description}
      checked={granted}
      onCheckedChange={handleToggle}
      disabled={isPending}
      error={failed ? "Couldn't save that — please try again." : undefined}
    />
  );
}
