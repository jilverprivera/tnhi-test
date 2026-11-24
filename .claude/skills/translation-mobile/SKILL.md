---
name: translation-mobile
description: i18n rules for Docket on small screens and the installed PWA (no native app; folder name is historical) — short Spanish label variants for codes in compact UI, manifest name/description in Spanish, offline/install/update prompts copy, and accessible labels for icon-only controls. Use when adding text that appears in phone layouts, the tab bar, sheets, the manifest or PWA prompts.
---

# Skill — i18n for compact UI and the PWA

> Base rules: `translation-web` (Spanish labels over English `UPPER_SNAKE_CASE` codes, typed dictionaries in `web/src/shared/i18n/`, nothing hardcoded).

## Short labels

Phone cards, chips and the tab bar have little room. When a label does not fit, add a `short` variant instead of truncating in CSS:

```ts
export const STATUS_LABELS: Record<DocumentStatus, { label: string; short: string }> = {
  NEEDS_REVIEW: { label: "Requiere revisión", short: "Revisar" },
  READY: { label: "Listo para radicar", short: "Listo" },
  ...
};
```

Use `short` only in compact layouts; the full label stays available as `title`/`aria-label`.

## PWA strings (`app/manifest.ts` + `shared/i18n/es.ts`)

- Manifest: `name` "Docket · Radicación TAC", `short_name` "Docket", Spanish `description`; `lang: "es-CO"`.
- Offline banner, "datos de <hora>" (last updated), install prompt, "nueva versión disponible" update prompt.
- Offline-disabled action explanation ("Sin conexión: no se puede radicar").

## Accessibility

- Icon-only buttons (tab bar, sheet close, batch select) need a Spanish `aria-label` from i18n.
- `<html lang="es-CO">`.

## Checklist

| # | Check |
|---|---|
| 1 | Compact UI uses `short` variants, full label in `aria-label`/`title`? |
| 2 | Manifest and PWA prompts in Spanish from `shared/i18n`? |
| 3 | Icon-only controls labelled? |
| 4 | No hardcoded strings in phone variants? |
