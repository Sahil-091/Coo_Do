// Campus Connect — app-shell service worker
//
// Scope (Phase 14): make the public install shell and previously downloaded
// static assets reachable offline without ever copying a student's private
// pages, check-ins, journal entries, or API responses into Cache Storage.
//
// What this DOES do:
//  - Precaches a small set of stable, non-hashed routes/assets on install.
//  - Runtime-caches only immutable Next build assets and public icons that
//    have already been fetched.
//  - Falls back to the public offline page for a failed navigation.
//
// What this does NOT do:
//  - It deliberately cannot submit or queue check-ins, attempts, journal
//    entries, reports, or RSVPs offline. Those are sensitive actions whose
//    server-side validation must run before a record is created.
//  - A protected page is never stored as an offline response. Once loaded,
//    its already-running client UI remains usable for local navigation, but
//    server-backed actions clearly require a connection.

const CACHE_VERSION = "v2";
const SHELL_CACHE = `campus-connect-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `campus-connect-runtime-${CACHE_VERSION}`;

const SHELL_URLS = [
  "/offline",
  "/manifest.webmanifest",
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

  // Never cache navigations. App routes are authenticated and can contain
  // sensitive student data; keeping their response in a shared browser cache
  // would make an offline convenience feature a privacy leak.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/offline"))
    );
    return;
  }

  const url = new URL(request.url);
  const isSafeStaticAsset =
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/icons/") ||
    ["/favicon.ico", "/icon.png", "/apple-icon.png", "/manifest.webmanifest"].includes(url.pathname);

  // Requests for RSC payloads, API routes, images that may be personalized,
  // and every other URL pass through untouched.
  if (!isSafeStaticAsset) return;

  // Static assets can safely be retained after the student has loaded them,
  // which keeps the previously visited UI shell responsive on weak Wi-Fi.
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
