---
name: testing-mobile
description: Testing the Docket frontend on small viewports and as a PWA (no native app; folder name is historical) — Playwright device emulation projects (phone, tablet, desktop), offline tests with context.setOffline, installability/manifest checks, Jest tests for viewport and online-status hooks, Lighthouse PWA. All runs go through ./scripts/harness-verify.sh with workers=1. Use when testing responsive layouts, offline behavior or the PWA.
---

# Skill — Small-viewport and PWA testing

## Tools

- **Playwright** device emulation for layouts and flows.
- **Jest + RTL** for hooks and adaptive components (`useMediaQuery`, `useOnlineStatus`, `InboxCardList`).
- **Lighthouse** (manual or CI) for PWA/accessibility scores.

## Playwright projects (`frontend/playwright.config.ts`)

```ts
workers: 1,
fullyParallel: false,
projects: [
  { name: "desktop-chrome", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
  { name: "tablet-ipad",    use: { ...devices["iPad (gen 7)"] } },
  { name: "phone-iphone",   use: { ...devices["iPhone 13"] } },
  { name: "phone-pixel",    use: { ...devices["Pixel 7"] } },
]
```

Phone-only specs: `e2e/<flow>.mobile.spec.ts`, filtered to phone projects.

## What to test

| Area | Test |
|---|---|
| Layout | At 375 px: inbox shows cards, no horizontal scroll (`document.documentElement.scrollWidth <= innerWidth`), batch bar visible |
| Touch | Primary actions have a bounding box >= 44x44 |
| Navigation | Bottom tab bar reaches inbox, ledger, deadlines, settings |
| Offline | Load deadlines online, `context.setOffline(true)`, reload: cached data + offline banner; approve buttons disabled |
| PWA | `/manifest.webmanifest` served with name, icons, `display: standalone`; service worker registers in a production build |
| Hooks | `useOnlineStatus` reacts to `online`/`offline` events; `useMediaQuery` SSR default |

Service-worker tests need a production build (`pnpm build` + `pnpm start` via Playwright `webServer`).

## Running (HARD RULE)

Never run Playwright or Jest outside the harness or with parallel workers:

```bash
./scripts/harness-verify.sh --e2e                                   # changed specs, --workers=1
./scripts/harness-verify.sh frontend/e2e/deadlines.mobile.spec.ts   # explicit spec
./scripts/harness-verify.sh --frontend                              # jest batches, --maxWorkers=1
```

`--e2e --full` only when the user asks.

## Definition of done

- Layout verified on phone, tablet and desktop projects.
- Offline read views and disabled mutations tested.
- Lighthouse PWA and Accessibility >= 90 recorded in `impl_<topic>.md`.
