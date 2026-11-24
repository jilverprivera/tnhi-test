---
name: mobile-forms-with-react-hook-form-and-zod-mobile
description: Touch-friendly forms for the Docket frontend on phones and tablets (no native app; folder name is historical) using react-hook-form + zod — the document correction form, send-to-review note and settings — with correct inputmode/autocomplete, large targets, sticky submit, Spanish i18n errors and offline-disabled submission. Use when building or changing any form that must work well on small touch screens.
---

# Skill — Forms on touch devices (react-hook-form + zod)

> Base rules: `forms-web` (RHF + `zodResolver`, schemas in `features/<f>/model/schemas.ts`, form hook `use<Name>Form.ts`, codes as values, Spanish labels, API error codes mapped to fields).

## Rules

1. Every form uses `react-hook-form` + zod; no per-field `useState`, no inline validation.
2. Default values always provided (the system proposal pre-fills corrections, so on a phone the clerk changes only what is wrong).
3. Error messages from `shared/i18n/form-errors.ts`, shown inline under the field.

## Inputs for touch

| Field | Attributes |
|---|---|
| NIT, invoice total, ID numbers | `inputMode="numeric"`, `autoComplete="off"` |
| Due date, holidays | native `type="date"` (opens the OS picker) |
| Department, action, document type | shadcn `Select` (or native `select` on phones) with Spanish labels, code values |
| Notes | `textarea` with `enterKeyHint="done"` |
| Search | `type="search"`, `enterKeyHint="search"` |

- Font size >= 16 px (avoids iOS zoom); controls >= 44 px tall; labels above inputs (not placeholders as labels).
- One column on phones; group long forms in sections (Clasificación, Datos extraídos, Nota).

## Submit

- Sticky submit bar at the bottom on phones (`BatchApproveStickyBar`-style) with safe-area padding; disabled while `isSubmitting`.
- Offline (`useOnlineStatus`): submit disabled with the Spanish explanation; never queue a correction or approval for later.
- On error, scroll and focus the first invalid field.

## Checklist

| # | Check |
|---|---|
| 1 | RHF + zodResolver; schema in `model/schemas.ts`? |
| 2 | Correct `inputMode` / `type` / `enterKeyHint` per field? |
| 3 | >= 16 px text, >= 44 px controls, single column on phones? |
| 4 | Sticky submit, disabled while submitting and offline? |
| 5 | Errors from i18n, focus to first invalid field? |
| 6 | Jest tests for the schema; Playwright phone test for the form? |
