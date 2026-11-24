/// <reference lib="webworker" />
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist";
import { CacheFirst, ExpirationPlugin, NetworkFirst, Serwist, StaleWhileRevalidate } from "serwist";

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined;
  }
}

declare const self: ServiceWorkerGlobalScope;

// Offline: only read views (deadlines, ledger) are kept, network first. Approvals, corrections and
// original documents are never cached or queued — they need the server.
const READ_VIEWS = /^\/(deadlines|ledger)(\/|$)/;

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: [
    {
      matcher: ({ request, url, sameOrigin }) => sameOrigin && request.mode === "navigate" && READ_VIEWS.test(url.pathname),
      handler: new NetworkFirst({ cacheName: "docket-read-views", networkTimeoutSeconds: 4 }),
    },
    {
      matcher: ({ url, sameOrigin }) => sameOrigin && url.pathname.startsWith("/_next/static/"),
      handler: new CacheFirst({ cacheName: "docket-static" }),
    },
    {
      matcher: ({ request, sameOrigin }) => sameOrigin && (request.destination === "font" || request.destination === "image"),
      handler: new StaleWhileRevalidate({
        cacheName: "docket-assets",
        plugins: [new ExpirationPlugin({ maxEntries: 64, maxAgeSeconds: 30 * 24 * 60 * 60 })],
      }),
    },
  ],
  fallbacks: {
    entries: [{ url: "/offline", matcher: ({ request }) => request.destination === "document" }],
  },
});

serwist.addEventListeners();
