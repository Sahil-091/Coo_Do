"use client";

import { useEffect } from "react";

/**
 * Registers the app-shell service worker (public/sw.js) on mount.
 * Renders nothing. Mounted once from the root layout.
 *
 * The worker only retains public shell/static assets. It intentionally never
 * caches protected route responses or API data on the device.
 */
export function RegisterServiceWorker() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;

    navigator.serviceWorker
      .register("/sw.js", { scope: "/", updateViaCache: "none" })
      .catch((err) => {
        console.error("Service worker registration failed:", err);
      });
  }, []);

  return null;
}
