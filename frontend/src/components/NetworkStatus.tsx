"use client";

import { WifiOff } from "lucide-react";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";

export function NetworkStatus() {
  const isOnline = useNetworkStatus();

  if (isOnline) return null;

  return (
    <div
      role="status"
      className="flex items-center gap-2 border-b border-lamp/20 bg-lamp-tint px-4 py-2 text-sm text-ink md:px-7"
    >
      <WifiOff className="h-4 w-4 shrink-0 text-lamp" aria-hidden="true" />
      You&rsquo;re offline. You can keep reading what is already open, but new changes will not save until you reconnect.
    </div>
  );
}
