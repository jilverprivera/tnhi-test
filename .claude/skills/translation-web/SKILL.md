---
name: translation-web
description: Enforces Docket's frontend i18n — the API speaks English UPPER_SNAKE_CASE codes and the UI shows Spanish labels from typed dictionaries in web/src/shared/i18n, with no hardcoded copy in components. Use when adding user-facing text, a new status/reason/error code, or any translation work in web/.
---

# Skill — i18n (Spanish UI over English codes)

## Model

- The backend returns English codes (`NEEDS_REVIEW`, `EMAIL_ACCOUNT_MISMATCH`, `DOCUMENT_NOT_FOUND`).
- The UI language is **Spanish (es-CO)**. Code stays in English; only label values are Spanish.
- Labels are imported from `@/shared/i18n/es`; adding English later means adding a sibling module and a selector.

## Source of truth

```
web/src/shared/i18n/
  es.ts                 # one module today:
                        #   documentTypeLabel, departmentLabel, actionLabel, statusLabel,
                        #   ledgerStatusLabel, deadlineStateLabel, outboxKindLabel, roleLabel  (Record<Code, string>)
                        #   extractionMethodLabel, reasonLabel + describeReason(), errorLabel + describeError()  (Record<string, ...>)
                        #   copy  (UI copy per area: nav, inbox, ledger, ...)
```

Split into per-namespace files (`reason-codes.ts`, `error-codes.ts`, ...) only when `es.ts` becomes hard to navigate; there is no `index.ts`/`t()` helper or locale switch today.

Enum dictionaries are typed `Record<Code, string>` so a new enum value without a label fails `pnpm build`. Reason and error codes are open `Record<string, ...>`: a missing label is not a build error, so add it in the same change.

## Rules (HARD)

- No hardcoded user-visible strings in `app/`, `features/` or `shared/ui/`: titles, labels, placeholders, empty/loading/error states, toasts, aria-labels, metadata titles.
- Every new backend code gets a Spanish label in the same change; unknown codes fall back to the raw code (`describeReason`) or a generic message (`describeError`).
- Dates and numbers formatted with `Intl` in `es-CO` and `America/Bogota` (`shared/lib/format.ts`: `formatDate`, `formatDateTime`, `formatMoney`); money in COP.
- Spanish labels use the client's vocabulary (radicado, dependencia, vence, devolver al remitente) — consistent with the Excel ledger.
- Reuse keys before adding near-duplicates in `copy`.

## Checklist

- New visible text in `shared/i18n`, none hardcoded?
- New codes labelled; `Record` types still exhaustive?
- Dates/numbers via `Intl` es-CO?
- Feature docs list the new codes with English and Spanish meaning (`docs/en`, `docs/es`)?
