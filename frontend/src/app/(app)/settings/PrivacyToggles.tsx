"use client";

import { useState, useTransition } from "react";
import { ToggleRow } from "@/components/ui/ToggleRow";
import { updatePrivacySettingsAction } from "@/lib/auth/actions";

type PrivacyKey = "profileVisibleInMatching" | "displayNameVisibleInRooms";

const ITEMS: { key: PrivacyKey; title: string; description: string }[] = [
  {
    key: "profileVisibleInMatching",
    title: "Visible in matching",
    description:
      "Lets Find Someone Like Me surface your profile to other students, once that feature is live.",
  },
  {
    key: "displayNameVisibleInRooms",
    title: "Show display name in rooms",
    description:
      'Shows your chosen display name (not just "Anonymous") in shared rooms, once those are live.',
  },
];

interface PrivacyTogglesProps {
  initialProfileVisibleInMatching: boolean;
  initialDisplayNameVisibleInRooms: boolean;
}

export function PrivacyToggles({
  initialProfileVisibleInMatching,
  initialDisplayNameVisibleInRooms,
}: PrivacyTogglesProps) {
  const [values, setValues] = useState<Record<PrivacyKey, boolean>>({
    profileVisibleInMatching: initialProfileVisibleInMatching,
    displayNameVisibleInRooms: initialDisplayNameVisibleInRooms,
  });
  const [failed, setFailed] = useState(false);
  const [isPending, startTransition] = useTransition();

  function handleToggle(key: PrivacyKey) {
    const previous = values;
    const next = { ...values, [key]: !values[key] };
    setValues(next);
    setFailed(false);

    startTransition(async () => {
      const formData = new FormData();
      formData.set("profileVisibleInMatching", String(next.profileVisibleInMatching));
      formData.set("displayNameVisibleInRooms", String(next.displayNameVisibleInRooms));
      const result = await updatePrivacySettingsAction({}, formData);
      if (result.error) {
        setValues(previous);
        setFailed(true);
      }
    });
  }

  return (
    <div className="flex flex-col gap-3">
      {ITEMS.map((item) => (
        <ToggleRow
          key={item.key}
          title={item.title}
          description={item.description}
          checked={values[item.key]}
          onCheckedChange={() => handleToggle(item.key)}
          disabled={isPending}
          error={failed ? "Couldn't save that — please try again." : undefined}
        />
      ))}
    </div>
  );
}
