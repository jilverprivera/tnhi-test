---
name: performance-mobile
description: Mobile-first performance for the Docket PWA (no native app; folder name is historical) — budgets for mid-range phones on slow networks, JS bundle size, skeletons, lazy-loaded document viewer, pagination and list rendering, service-worker caching, Core Web Vitals. Use when optimizing load or interaction speed on phones, or adding heavy UI to small-screen views.
---

# Skill — Performance on phones

> Base rules: `performance-web`.

## Budgets (mid-range Android, "Fast 4G" throttling)

- LCP < 2.5 s, INP < 200 ms, CLS < 0.1 on inbox, ledger and deadlines.
- First-load JS for `/inbox` and `/deadlines` kept small: no PDF viewer, no chart libraries, no date libraries beyond `Intl`.

## Rules

1. **Skeletons** for every async area (same shape as content; no layout shift when data arrives).
2. **Lazy-load** the original-document viewer (`next/dynamic`, `ssr: false`) and open it on demand on phones (tab or sheet).
3. **Lists**: server pagination (`limit`/`offset`) with "Cargar más"; avoid rendering hundreds of cards; virtualize only if needed.
4. **Server Components** for read views; minimal client JS on phones.
5. **Caching**: service worker serves cached read views instantly (NetworkFirst with short timeout), static assets CacheFirst; show "last updated".
6. **Images/icons**: SVG icons from one library, tree-shaken imports; no icon fonts.
7. **Interactions**: debounce search (300 ms); avoid re-rendering the whole list on selection (memoize card items when profiling shows waste).

## Measuring

- Lighthouse mobile preset on a production build; record scores in `impl_<topic>.md`.
- `next build` output for first-load JS per route; flag regressions.

## Checklist

| # | Check |
|---|---|
| 1 | Skeletons without layout shift? |
| 2 | Viewer lazy-loaded and on demand? |
| 3 | Lists paginated? |
| 4 | First-load JS within budget; no heavy libs in core routes? |
| 5 | Lighthouse mobile >= 90 recorded? |
