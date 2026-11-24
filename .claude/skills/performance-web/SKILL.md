---
name: performance-web
description: Enforces performance and UX rules for the Docket Next.js frontend — Server Components by default, skeletons for async content, lazy-loaded heavy viewers, paginated lists, Lighthouse targets. Use when optimizing pages, adding async views, lists, the document viewer, or checking Core Web Vitals in web/.
---

# Skill — Performance and UX (web)

## Rules

- **Skeletons for every async content area**: `<Name>Skeleton.tsx` next to the component, same shape as the real content; use `loading.tsx` in routes for streaming. Spinners only inside buttons.
- **Server Components by default**; `"use client"` only for interactive leaves. Fetch read views (ledger, deadlines) on the server.
- **Lazy-load heavy client code**: the PDF/original viewer in `document-review` via `next/dynamic` with a skeleton; never in the initial inbox bundle.
- **Lists**: paginate from the API (`limit`/`offset`) and filter server-side; virtualize only if a list exceeds a few hundred rows. Known gap: the API does not paginate yet (`/api/inbox`, `/api/ledger` return everything); add `limit`/`offset` on both sides together.
- **Images/fonts**: `next/image` sized; `next/font` with `display: swap`.
- **Memoization** only where profiling shows wasted renders (large tables).
- **Metadata**: each route sets `title` (Spanish, from i18n). The app is internal: `robots: noindex`.

## Targets

- Lighthouse Performance, Accessibility, Best Practices and PWA >= 90 on inbox, ledger and deadlines.
- Inbox interactive in < 2 s on a mid-range phone profile (see `performance-mobile`).

## Checklist

- Skeleton for each async area? Viewer lazy-loaded?
- Server Components where possible?
- Lists paginated server-side?
- Lighthouse >= 90?
