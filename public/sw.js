const CACHE_NAME = "sph-shell-v33";
const CORE_ASSETS = [
  "/",
  "/index.html",
  "/styles.css",
  "/app.js",
  "/date-utils.mjs",
  "/account-client.mjs",
  "/journey-sync.mjs",
  "/offline-support.mjs",
  "/journey-backup.mjs",
  "/manifest.webmanifest",
  "/favicon-32.png",
  "/apple-touch-icon.png",
  "/icon-512.png",
  "/data/meditations.json",
  "/data/daily_support.json",
  "/privacidade/index.html",
  "/expo/index.html",
  "/expo/styles.css",
  "/expo/page.js",
  "/expo/hero-banner.jpg",
  "/expo/sandro-logo-white.png",
  "/expo/sandro-profile.png"
];

function navigationFallback(pathname) {
  if (pathname.startsWith("/expo")) return "/expo/index.html";
  if (pathname.startsWith("/privacidade")) return "/privacidade/index.html";
  return "/index.html";
}

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS)));
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
    )),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(request));
    return;
  }

  if (request.mode === "navigate") {
    const fallback = navigationFallback(url.pathname);
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(fallback, copy));
          }
          return response;
        })
        .catch(async () => (await caches.match(fallback)) || caches.match("/index.html")),
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);
      return cached || network;
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const requestedUrl = new URL(event.notification.data?.url || "/#meditacao", self.location.origin);
  const targetUrl = requestedUrl.origin === self.location.origin
    ? `${requestedUrl.pathname}${requestedUrl.search}${requestedUrl.hash}`
    : "/#meditacao";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      const existing = windows.find((client) => new URL(client.url).origin === self.location.origin);
      if (existing) {
        existing.navigate(targetUrl);
        return existing.focus();
      }
      return clients.openWindow(targetUrl);
    }),
  );
});

self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data?.json() || {};
  } catch {
    payload = { body: event.data?.text() || "A meditação de hoje está pronta." };
  }
  event.waitUntil(self.registration.showNotification(payload.title || "Só Por Hoje", {
    body: payload.body || "A meditação de hoje está pronta. Um dia de cada vez.",
    icon: "/icon-512.png",
    badge: "/favicon-32.png",
    tag: "sph-daily-reminder",
    data: { url: payload.url || "/#meditacao" },
  }));
});
