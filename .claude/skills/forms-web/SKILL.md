---
name: forms-web
description: Standardizes Docket frontend forms with react-hook-form + zod — document correction, send-to-review note, settings (holidays, catalog reload), ledger search — with schemas in feature model/, Spanish error messages from i18n, and API error codes mapped to fields. Use when creating or changing any form in frontend/.
---

# Skill — Forms (react-hook-form + zod)

## Rules

- Every form uses `react-hook-form` with `zodResolver`; all validation lives in zod schemas.
- No `useState` per field; no inline validation in components.
- Default values always provided (the system proposal pre-fills the correction form).

## Placement

| Piece | Location |
|---|---|
| Zod schema + inferred type | `features/<f>/model/schemas.ts` |
| Form hook (`useForm`, submit, reset, server errors) | `features/<f>/hooks/use<Name>Form.ts` |
| Submit call | `features/<f>/api/<verb>-<noun>.ts` |
| Form UI | `features/<f>/components/organisms/<Name>Form.tsx` built from `shared/ui` primitives (`form`, `input`, `select`) |

Main forms:
- `document-review`: `DocumentCorrectionForm` — document type, department, action, due date, extracted fields (NIT, invoice number, total, purchase order), note. Values are `UPPER_SNAKE_CASE` codes; selects show Spanish labels.
- `document-review`: send to review with a mandatory note.
- `settings`: extra holidays (ISO dates), catalog reload confirmation.
- `ledger`: search box (URL search params, debounced).

## Validation and errors

- Schema messages are i18n keys resolved to Spanish (`shared/i18n/form-errors.ts`), never hardcoded text.
- NIT validated with the same verification-digit rule as the backend (shared helper in `shared/lib/nit.ts`), but the backend remains the authority.
- API errors: `ApiError.code` -> `form.setError(field, ...)` when `params.field` is present, otherwise a form-level alert with the code's Spanish label.
- Submit button disabled while `isSubmitting`; show inline progress on the button only.

## Accessibility

- Every input has a visible `<label>`; errors linked with `aria-describedby`; focus moves to the first invalid field on submit.
- Touch-friendly rules for small screens: `mobile-forms-with-react-hook-form-and-zod-mobile`.

## Checklist

- RHF + zodResolver; schema in `model/schemas.ts`?
- Defaults from the proposal; codes as values, Spanish labels in the UI?
- Server error codes mapped to fields or form alert?
- Tests: schema valid/invalid cases and submit behavior (Jest + RTL)?
