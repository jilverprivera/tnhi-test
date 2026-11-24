"use client";

import { SerwistProvider } from "@serwist/next/react";

/** Registers the service worker in production builds only (dev keeps fresh code). */
export function ServiceWorkerProvider({ children }: { children: React.ReactNode }) {
  return (
    <SerwistProvider swUrl="/sw.js" disable={process.env.NODE_ENV !== "production"} reloadOnOnline={false}>
      {children}
    </SerwistProvider>
  );
}
