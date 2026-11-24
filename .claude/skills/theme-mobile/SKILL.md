---
name: theme-mobile
description: Theming rules for Docket on phones and as an installed PWA (no native app; folder name is historical) — light/dark theme-color meta, manifest colors, safe-area insets, touch target sizes, system color scheme, standalone display. Use when styling for small screens, changing brand colors, or adjusting how the installed PWA looks.
---

# Skill — Theme on small screens and the installed PWA

> Tokens and semantic classes: `theme-web` (closed Tailwind v4 `@theme` + shadcn layer). UI/UX direction: `/apple-design` and `/ui-ux-pro-max`.

## Light and dark in the OS chrome

- Root `layout.tsx` exports `viewport.themeColor` with two entries (`media: "(prefers-color-scheme: light)"` / `dark`) using the `background` token values from `tokens.css`.
- `app/manifest.ts` `theme_color` and `background_color` = light `background` (the splash screen); keep them in sync when tokens change.
- `next-themes` default `system`; the user override is stored locally and applied before paint (no flash).
- Status bar in standalone mode: `appleWebApp.statusBarStyle: "default"`.

## Touch and spacing

- Touch targets >= 44x44 px (`min-h-11 min-w-11`); spacing between adjacent targets >= 8 px.
- Body text >= 16 px on inputs to avoid iOS zoom.
- Sticky bars and the tab bar pad with `pb-[env(safe-area-inset-bottom)]`; the shell uses `viewport-fit=cover`.
- Hover-only affordances need a touch equivalent (visible buttons, not hover menus).

## Motion and materials

- Respect `prefers-reduced-motion` (Tailwind `motion-safe:` / `motion-reduce:`).
- Sheets and bars may use translucent `glass` surfaces only if contrast stays AA in both schemes.

## Rules

- Same semantic classes as desktop; no phone-only color tokens.
- Status colors from the single mapping in `theme-web`, always with icon + label (small screens cannot rely on color in a tiny dot).

## Checklist

| # | Check |
|---|---|
| 1 | `themeColor` for light and dark; manifest colors in sync with tokens? |
| 2 | Touch targets >= 44 px; inputs >= 16 px? |
| 3 | Safe-area insets on sticky UI? |
| 4 | Reduced motion respected? |
| 5 | Checked light and dark at 375 px? |
