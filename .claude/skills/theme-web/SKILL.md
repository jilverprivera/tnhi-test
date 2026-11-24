---
name: theme-web
description: Enforces Docket's closed Tailwind CSS v4 token system with a shadcn/ui semantic layer and light/dark themes (frontend/src/shared/theme/tokens.css), status colors for document states, and UI/UX direction from /apple-design and /ui-ux-pro-max. Use when styling any component, adding colors, tokens, dark mode, or theming in frontend/.
---

# Skill — Theme (Tailwind v4 tokens + shadcn, light + dark)

UI/UX direction: load the user-level skills **`/apple-design`** (restraint, typography, motion, materials) and **`/ui-ux-pro-max`** (palettes, accessibility, layout) when designing screens.

## Source of truth

- `frontend/src/shared/theme/tokens.css`, imported once from `app/globals.css`.
- Reference models (read-only, do not modify): `/Volumes/SSD/dev/resident-portal/packages/tokens/css/tokens.css` (closed `@theme`, semantic `@theme inline`) and `/Volumes/SSD/dev/ganaderiapp/tailwind.config.js` (light/dark role palettes).

## Structure of `tokens.css`

1. **Closed palette** — `@theme { --color-*: initial; --radius-*: initial; ... }` then the brand palette (e.g. `--color-harbor-50..950`, neutrals, success/warning/danger/info ramps). Tailwind's default palette does not exist: `bg-blue-500` produces nothing.
2. **Scales** — radius, typography (`--text-headline-md`, `--text-body-sm`, `--text-label-md` with line-height/weight), easing (`--ease-standard`).
3. **Semantic layer** — `@theme inline { --color-background: var(--background); --color-primary: var(--primary); ... }` with shadcn names (`background`, `foreground`, `card`, `popover`, `muted`, `accent`, `secondary`, `border`, `input`, `ring`, `primary`, `destructive`) plus Docket roles (`success`, `warning`, `danger`, `info`, each with `-foreground` and `-soft`).
4. **Schemes** — `:root { --background: ...; }` for light and `.dark { ... }` for dark (class strategy via `next-themes`, default `system`).

## Document status colors (one mapping, used everywhere)

| Code | Role |
|---|---|
| `READY` | `success` |
| `NEEDS_REVIEW` | `warning` |
| `HOLD_FOR_VERIFICATION` | `danger` |
| `RETURN_TO_SENDER` | `info` |
| `DO_NOT_FILE`, `DISCARDED` | `muted` |
| `REPLY_WITH_EXISTING_NUMBER` (duplicate) | `secondary` |
| urgent due date | `danger` |

Defined once in `shared/ui/molecules/StatusBadge` (via `cva`); color is never the only signal (icon + label too).

## Rules (HARD)

- Components use semantic classes only (`bg-background`, `text-foreground`, `bg-warning-soft text-warning-foreground`), never palette steps or hex values. Then dark mode comes for free; no `dark:` overrides scattered in components.
- New colors go into `tokens.css` (palette + semantic role for both schemes), never inline.
- shadcn primitives are themed through the semantic variables, not by editing their class lists per use.
- Contrast WCAG AA in both schemes (4.5:1 text, 3:1 large text and UI).

## Checklist

- Only semantic token classes; no hex, no default Tailwind palette?
- Verified light and dark?
- Status colors from the single mapping, with icon/label?
- Contrast AA?
- PWA `theme-color` updated if brand colors changed (`theme-mobile`)?
