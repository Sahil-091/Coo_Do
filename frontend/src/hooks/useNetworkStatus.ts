"use client";

import { useEffect, useState } from "react";

/**
 * Browser connectivity is advisory: a successful server action is still the
 * authority. It lets sensitive flows fail early and explain why nothing was
 * saved instead of pretending an offline action has been recorded.
 */
export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const sync = () => setIsOnline(navigator.onLine);
    sync();
    window.addEventListener("online", sync);
    window.addEventListener("offline", sync);
    return () => {
      window.removeEventListener("online", sync);
      window.removeEventListener("offline", sync);
    };
  }, []);

  return isOnline;
}
