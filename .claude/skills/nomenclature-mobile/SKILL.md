---
name: nomenclature-mobile
description: Naming conventions for Docket's responsive and PWA artifacts (no native app; folder name is historical) — manifest and service worker files, phone-variant components (CardList, Sheet, StickyBar), viewport and online-status hooks, Playwright device projects. Use when naming files or symbols related to small screens, PWA, offline or installability.
---

# Skill — Responsive / PWA nomenclature

> Base rules: `nomenclature-web`. Everything in English.

## Files

| Kind | Pattern | Example |
|---|---|---|
| Web app manifest | `app/manifest.ts` | |
| Service worker | `app/sw.ts` | |
| Icons | `public/icons/icon-<size>.png`, `icon-maskable-<size>.png` | `icon-512.png` |
| Phone list variant of a table | `<Thing>CardList.tsx` | `InboxCardList.tsx` |
| Card item | `<Thing>Card.tsx` | `DeadlineCard.tsx` |
| Bottom sheet | `<Purpose>Sheet.tsx` | `DocumentOriginalSheet.tsx` |
| Sticky action bar | `<Purpose>StickyBar.tsx` | `BatchApproveStickyBar.tsx` |
| Navigation | `BottomTabBar.tsx`, `AppSidebar.tsx` | |
| Viewport / PWA hooks | `use-<name>.ts` in `shared/lib/` exporting `use<Name>` | `use-media-query.ts` -> `useMediaQuery`, `use-online-status.ts` -> `useOnlineStatus`, `use-install-prompt.ts` -> `useInstallPrompt` |
| E2E device spec | `e2e/<flow>.mobile.spec.ts` when phone-only | `e2e/deadlines.mobile.spec.ts` |

## Rules

- Do **not** suffix components with `Mobile` / `Desktop`; name by representation (`CardList` vs `Table`, `Sheet` vs `Pane`).
- Breakpoint names are Tailwind's (`sm`, `md`, `lg`); no custom names in code.
- Playwright projects: `desktop-chrome`, `tablet-ipad`, `phone-iphone`, `phone-pixel`.
- Cache names in the service worker: `docket-<purpose>-v<n>` (`docket-read-views-v1`).

## Checklist

- Component named by representation, not by device?
- PWA files at the paths above?
- Hooks in `shared/lib/use-*.ts`?
- Playwright project names consistent?
