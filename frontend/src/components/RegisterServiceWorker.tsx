"use client";

import { useEffect } from "react";

/**
 * Registers the app-shell service worker (public/sw.js) on mount.
 * Renders nothing. Mounted once from the root layout.
 *
 * Per Next.js's own PWA guide, this is dependency-free on purpose —
 * see /public/sw.js for what it actually caches, and the root README
 * for why we didn't reach for Serwist/Workbox at this scaffold stage.
 */
export function RegisterServiceWorker() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;

    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .catch((err) => {
        console.error("Service worker registration failed:", err);
      });
  }, []);

  return null;
}
