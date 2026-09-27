const CACHE_NAME = "sph-shell-v64";
const PUSH_TITLE = "Só Por Hoje";
const PUSH_BODY = "A meditação de hoje está pronta. Um dia de cada vez.";
const PUSH_DEFAULT_URL = "/#meditacao";
const CORE_ASSETS = [
  "/",
  "/index.html",
  "/styles.css",
  "/app.js",
  "/date-utils.mjs",
  "/privacy-copy.mjs",
  "/share-format.mjs",
  "/editorial-links.mjs",
  "/help-links.mjs",
  "/account-client.mjs",
  "/journey-sync.mjs",
  "/journey-sync-cursor.mjs",
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
const CORE_PATHS = new Set(CORE_ASSETS.map((asset) => new URL(asset, self.location.origin).pathname));

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
    (async () => {
      const keys = await caches.keys();
      await Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)),
      );
      await self.clients.claim();
    })(),
  );
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

  if (url.pathname.startsWith("/admin")) {
    event.respondWith(fetch(request, { cache: "no-store" }));
    return;
  }

  if (request.mode === "navigate") {
    const fallback = navigationFallback(url.pathname);
    event.respondWith(
      (async () => {
        try {
          const response = await fetch(request);
          if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(fallback, response.clone());
          }
          return response;
        } catch {
          return (await caches.match(fallback)) || caches.match("/index.html");
        }
      })(),
    );
    return;
  }

  if (CORE_PATHS.has(url.pathname)) {
    event.respondWith(
      (async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        const response = await fetch(request);
        if (response.ok) {
          const cache = await caches.open(CACHE_NAME);
          await cache.put(request, response.clone());
        }
        return response;
      })(),
    );
    return;
  }

  event.respondWith(
    (async () => {
      const cached = await caches.match(request);
      const network = fetch(request)
        .then(async (response) => {
          if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, response.clone());
          }
          return response;
        });
      if (!cached) return network;
      event.waitUntil(network.then(() => undefined).catch(() => undefined));
      return cached;
    })(),
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
  let requestedUrl = PUSH_DEFAULT_URL;
  try {
    const payload = event.data?.json() || {};
    if (typeof payload.url === "string") requestedUrl = payload.url;
  } catch {
    // Text from a push payload is intentionally ignored on the lock screen.
  }
  let targetUrl = PUSH_DEFAULT_URL;
  try {
    const parsedUrl = new URL(requestedUrl, self.location.origin);
    if (parsedUrl.origin === self.location.origin) {
      targetUrl = `${parsedUrl.pathname}${parsedUrl.search}${parsedUrl.hash}`;
    }
  } catch {
    targetUrl = PUSH_DEFAULT_URL;
  }
  event.waitUntil(self.registration.showNotification(PUSH_TITLE, {
    body: PUSH_BODY,
    icon: "/icon-512.png",
    badge: "/favicon-32.png",
    tag: "sph-daily-reminder",
    data: { url: targetUrl },
  }));
});
