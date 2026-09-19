"use client";

import { Download } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export function InstallPrompt() {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    const standalone = window.matchMedia("(display-mode: standalone)");
    const syncStandalone = () => setIsStandalone(standalone.matches || (navigator as Navigator & { standalone?: boolean }).standalone === true);
    const onBeforeInstall = (event: Event) => {
      event.preventDefault();
      setPromptEvent(event as BeforeInstallPromptEvent);
    };

    // Defer the initial browser-only values until after hydration. Besides
    // avoiding an SSR/client mismatch, this keeps the effect subscription
    // focused on external browser events.
    const initialSync = window.setTimeout(() => {
      setIsIOS(/iPad|iPhone|iPod/.test(navigator.userAgent));
      syncStandalone();
    }, 0);
    standalone.addEventListener("change", syncStandalone);
    window.addEventListener("beforeinstallprompt", onBeforeInstall);
    return () => {
      window.clearTimeout(initialSync);
      standalone.removeEventListener("change", syncStandalone);
      window.removeEventListener("beforeinstallprompt", onBeforeInstall);
    };
  }, []);

  async function install() {
    if (!promptEvent) return;
    await promptEvent.prompt();
    await promptEvent.userChoice;
    setPromptEvent(null);
  }

  if (isStandalone || (!isIOS && !promptEvent)) return null;

  return (
    <aside className="mx-4 mt-4 rounded-lg border border-border-subtle bg-paper-raised p-4 shadow-sm md:mx-7" aria-label="Install Coo Do">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm leading-5 text-ink-muted">
          {isIOS
            ? "Add Coo_Do to your Home Screen: tap Share, then Add to Home Screen."
            : "Install Coo_Do for a focused, full-screen experience and reliable access to the saved app shell."}
        </p>
        {promptEvent && <Button type="button" size="sm" onClick={install}><Download className="h-4 w-4" aria-hidden="true" /> Install</Button>}
      </div>
    </aside>
  );
}
