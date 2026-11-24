---
name: translation-web
description: Enforces Docket's frontend i18n — the API speaks English UPPER_SNAKE_CASE codes and the UI shows Spanish labels from typed dictionaries in frontend/src/shared/i18n, with no hardcoded copy in components. Use when adding user-facing text, a new status/reason/error code, or any translation work in frontend/.
---

# Skill — i18n (Spanish UI over English codes)

## Model

- The backend returns English codes (`NEEDS_REVIEW`, `INVOICE_ACCOUNT_MISMATCH`, `DOCUMENT_NOT_FOUND`).
- The UI language is **Spanish (es-CO)**. Code stays in English; only label values are Spanish.
- Structure keeps a locale key so English can be added later without touching components.

## Source of truth

```
frontend/src/shared/i18n/
  index.ts              # t(), label helpers, locale = "es"
  common.ts             # buttons, empty/loading/error states
  document-types.ts     # Record<DocumentType, string>
  departments.ts        # Record<Department, string>
  actions.ts            # Record<Action, string>
  statuses.ts           # Record<DocumentStatus, string>
  reason-codes.ts       # Record<ReasonCode, { label: string; help?: string }>
  error-codes.ts        # Record<ErrorCode, string>
  form-errors.ts
  <feature>.ts          # copy per feature: inbox.ts, document-review.ts, ledger.ts, deadlines.ts, settings.ts
```

Dictionaries are typed `Record<Code, string>` so a new code without a label fails `pnpm build`.

## Rules (HARD)

- No hardcoded user-visible strings in `app/`, `features/` or `shared/ui/`: titles, labels, placeholders, empty/loading/error states, toasts, aria-labels, metadata titles.
- Every new backend code gets a Spanish label in the same change; unknown codes render a generic fallback and are logged.
- Dates and numbers formatted with `Intl` in `es-CO` and `America/Bogota` (`shared/lib/dates.ts`); money in COP.
- Spanish labels use the client's vocabulary (radicado, dependencia, vence, devolver al remitente) — consistent with the Excel ledger.
- Reuse keys before adding near-duplicates; `common.ts` only for strings used in 3+ places.

## Checklist

- New visible text in `shared/i18n`, none hardcoded?
- New codes labelled; `Record` types still exhaustive?
- Dates/numbers via `Intl` es-CO?
- Feature docs list the new codes with English and Spanish meaning (`docs/en`, `docs/es`)?
