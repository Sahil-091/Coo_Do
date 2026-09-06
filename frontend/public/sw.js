// Campus Connect — app-shell service worker
//
// Scope (Phase 0, R&D doc Section 18): make the app installable and keep
// the shell reachable offline. This is a hand-written, dependency-free
// worker, not Workbox/Serwist — see root README "Known limitations" for
// why, and when we'd reach for Serwist instead (Next.js's own
// recommendation for full precaching of hashed build output).
//
// What this DOES do:
//  - Precaches a small set of stable, non-hashed routes/assets on install.
//  - Runtime-caches same-origin GET responses as they're fetched (so pages
//    and hashed /_next/static/* chunks the user actually visited while
//    online become available offline afterwards).
//  - Falls back to the cached shell (and finally /offline) for navigations
//    that fail while offline.
//
// What this does NOT do:
//  - It does not precache every hashed build asset up front, so a route
//    the user never visited while online will not work on a cold offline
//    load. That requires build-time manifest generation (Serwist).
//  - It never intercepts cross-origin requests (core-api / safety-service
//    calls) — those are left to the app's own online/offline handling.

const CACHE_VERSION = "v1";
const SHELL_CACHE = `campus-connect-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `campus-connect-runtime-${CACHE_VERSION}`;

const SHELL_URLS = [
  "/",
  "/offline",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/icon-maskable-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== SHELL_CACHE && key !== RUNTIME_CACHE)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Only handle same-origin GET requests. Everything else (API calls,
  // POSTs, cross-origin) passes straight through untouched.
  if (request.method !== "GET" || new URL(request.url).origin !== self.location.origin) {
    return;
  }

  // Navigations: network-first, falling back to the cached page, then the
  // cached app shell, then the offline page.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          const shell = await caches.match("/");
          if (shell) return shell;
          return caches.match("/offline");
        })
    );
    return;
  }

  // Everything else same-origin: cache-first, then network with a
  // runtime-cache write, so assets visited while online become available
  // offline on the next load.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
    })
  );
});
