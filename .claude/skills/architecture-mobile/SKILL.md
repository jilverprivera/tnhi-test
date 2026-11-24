---
name: architecture-mobile
description: Mobile/responsive/PWA architecture of the Docket Next.js frontend (there is no native app; the folder name is historical) — mobile-first layouts per feature, app shell and navigation on small screens, Serwist service worker and manifest, offline caching of read views, installability, and the async UX contract. Use when building or changing layouts, navigation, PWA/offline behavior, or anything about how Docket works on phones and tablets.
---

# Skill — Mobile-first and PWA architecture

> There is **no native mobile app**. "Mobile" means the Next.js frontend on phones/tablets and as an installed PWA. All structure rules from `architecture-web` apply.

## Goal

The coordinator checks deadlines from her phone; the clerk may triage the inbox on a tablet. Every view works from 375 px up, is installable, and read views keep working offline.

## Breakpoints and layouts

Design mobile-first (base classes = phone), enhance with `md:` (768) and `lg:` (1024+). Verify at 375, 768 and 1440 px.

| Feature | Phone | Tablet / desktop |
|---|---|---|
| inbox | Card list (`InboxCardList`), status filter as segmented chips, batch approve in a sticky bottom bar | Table (`InboxTable`) with checkboxes and toolbar |
| document-review | Stacked: summary + reasons first, then fields, original in a tab or bottom sheet | Two panes: original viewer left, fields + reasons right |
| ledger | Search + card list, Excel download button | Table with column sort |
| deadlines | Grouped list: overdue / this week / next week, urgent first | Same groups in columns |
| settings | Single column | Single column, max width |

Same data, different organisms: switch with CSS (`hidden md:block`) when both are cheap, or render one organism that adapts. Never duplicate business logic per breakpoint.

## App shell and navigation

- `shared/ui/organisms/AppShell` (with `AppNav` `variant="tabbar" | "sidebar"`): bottom tab bar on phones (Bandeja, Libro, Vencimientos, Ajustes), sidebar on `lg:`.
- Respect safe areas (`env(safe-area-inset-*)`) in the shell and sticky bars.
- Back navigation uses real routes (`/documents/[id]`), so the browser/OS back gesture works.

## PWA (Serwist)

- `app/manifest.ts`: Spanish name/short name, `display: "standalone"`, `start_url: "/inbox"`, theme/background colors from tokens, maskable icons 192/512.
- `app/sw.ts` (Serwist) + `withSerwist` in `next.config`: precache the app shell; runtime caching:
  - `GET /ledger`, `GET /deadlines`, `GET /reports/weekly`: `NetworkFirst` with a short timeout, fallback to cache (read views available offline).
  - Static assets: `CacheFirst`.
  - Mutations (`POST` approve/correct/import): **never cached or queued**. Offline, the action is disabled with a message; nothing is filed without a live server.
- Show an offline banner (`useOnlineStatus`) and the "last updated" time on cached views.
- Disable the service worker in development.
- Data sensitivity: cache only what the read views need; no original documents in the SW cache.

## Async UX contract (every view)

- Loading -> skeleton with the shape of the content.
- Mutation -> inline progress on the trigger, disabled while pending.
- Error -> Spanish label of the error code, with retry.
- Empty -> meaningful empty state ("No hay documentos pendientes").

## Checklist

| # | Check |
|---|---|
| 1 | Works at 375 / 768 / 1440 px, mobile-first classes? |
| 2 | Touch targets >= 44x44 px; sticky actions respect safe areas? |
| 3 | Read views cached NetworkFirst; mutations never cached/queued? |
| 4 | Offline banner and disabled actions offline? |
| 5 | Manifest/installability intact? |
| 6 | Skeleton, error, empty states present? |
| 7 | Playwright device tests (`testing-mobile`)? |
| 8 | PWA behavior documented (`documentation-mobile`)? |
