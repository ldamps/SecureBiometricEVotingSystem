/**
 * Minimal service worker for PWA installability.
 *
 * Exists so the browser offers "Add to Home Screen".  The biometric
 * enrollment/verification pages then run in a standalone PWA context
 * where IndexedDB is persistent (not cleared with browser history).
 *
 * IMPORTANT: This SW intentionally does NOT cache navigation requests
 * (HTML pages).  Caching index.html caused blank-page bugs when deploys
 * changed the JS bundle hash — the stale cached HTML referenced a JS
 * file that no longer existed.  Only static assets (JS/CSS with
 * content-hash filenames) are cached.
 */

const CACHE_NAME = "evoting-pwa-v2";

// Immediately take control on install — no precache of HTML.
self.addEventListener("install", () => {
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

// Network-first for static assets only.  Navigation requests (HTML)
// always go straight to the network so the browser gets the latest
// index.html with the correct JS bundle hash.
self.addEventListener("fetch", (event) => {
  const { request } = event;

  // Skip non-GET, API calls, and navigation (HTML) requests.
  if (
    request.method !== "GET" ||
    request.url.includes("/api/") ||
    request.mode === "navigate"
  ) {
    return;
  }

  // Cache static assets (content-hashed) and ML model files (immutable).
  if (!request.url.includes("/static/") && !request.url.includes("/models/")) {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(request).then((cached) => {
        // Static assets have content hashes — cache-first is safe.
        if (cached) return cached;
        return fetch(request).then((response) => {
          cache.put(request, response.clone());
          return response;
        });
      }),
    ),
  );
});
