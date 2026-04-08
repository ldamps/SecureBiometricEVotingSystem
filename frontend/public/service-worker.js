/**
 * Minimal service worker for PWA installability.
 *
 * Caches the app shell so the "Add to Home Screen" prompt appears on
 * mobile browsers.  The biometric enrollment/verification pages then
 * run inside a standalone PWA context where IndexedDB is persistent
 * (not cleared with normal browser history).
 */

const CACHE_NAME = "evoting-pwa-v1";

// Cache the app shell on install.
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      cache.addAll(["/", "/index.html"])
    ),
  );
  self.skipWaiting();
});

// Clean up old caches on activate.
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)),
      ),
    ),
  );
  self.clients.claim();
});

// Network-first strategy: try network, fall back to cache.
self.addEventListener("fetch", (event) => {
  // Skip non-GET and API requests — always go to network.
  if (event.request.method !== "GET" || event.request.url.includes("/api/")) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request)),
  );
});
