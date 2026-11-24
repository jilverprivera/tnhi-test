---
name: structure-mobile
description: Responsive component placement for the Docket frontend (no native app; folder name is historical) — one component per file, where phone-specific variants (card lists, bottom sheets, sticky action bars, tab bar) live in the atomic layers, and how to avoid duplicating components per breakpoint. Use when creating or splitting components that behave differently on small screens.
---

# Skill — Responsive component structure

> All rules from `ui-structure-web` apply (one component per file, atomic layers, reuse-first gate). This skill adds the rules for small-screen variants.

## 1) One component per file (zero tolerance)

Applies equally to responsive variants: `InboxTable` and `InboxCardList` are two files; a phone-only row is its own molecule file, never a helper inside the table file.

## 2) Prefer one adaptive component

Before creating a phone variant, try to make one component adapt with Tailwind breakpoints (`flex-col md:flex-row`, `hidden md:table-cell`). Create a separate variant only when the structure is genuinely different (table vs cards, side pane vs bottom sheet).

## 3) Where variants live

| Variant | Layer | Bucket |
|---|---|---|
| Phone list representation of a feature table (`InboxCardList`, `LedgerCardList`) | organism | the feature |
| Single card (`InboxCard`, `DeadlineCard`) | molecule | the feature (shared if 2+ features) |
| Bottom sheet, sticky action bar, tab bar, offline banner | organism / molecule | `shared/ui` |
| `Sheet`, `Drawer` base | primitive | `shared/ui/primitives` (shadcn) |
| Layout switch between variants | template | the feature (`InboxTemplate`) |

The template decides which variant renders; organisms don't check viewport size themselves.

## 4) Choosing the variant

- CSS first: render both and hide one with `md:` classes when both are light.
- `useMediaQuery` (`shared/lib/use-media-query.ts`) only when rendering both is expensive (e.g. the document viewer); provide an SSR-safe default (phone) to avoid hydration mismatch.

## 5) Shared variant logic

Selection state, filters and data come from the feature hook (`useInboxSelection`), so table and cards share behavior; variants only render.

## Checklist

| # | Check |
|---|---|
| 1 | One component per file, variants included? |
| 2 | Tried a single adaptive component first? |
| 3 | Variant in the right layer and bucket? |
| 4 | Template chooses the variant; logic in a shared hook? |
| 5 | No hydration mismatch from viewport checks? |
