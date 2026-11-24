---
name: forms-web
description: Standardizes Docket frontend forms with react-hook-form + zod — document correction (today the only RHF form), discard reason, supplier master upload, login, ledger search — with schemas in feature model/, Spanish error messages from i18n, and API error codes mapped to fields. Use when creating or changing any form in web/.
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
| Form hook (`useForm`, submit, reset, server errors) | inside the form organism today (`CorrectionSheet.tsx`); extract to `features/<f>/hooks/use<Name>Form.ts` when it grows |
| Submit call | Server Action in `features/<f>/api/<f>-actions.ts` (e.g. `correctDocumentAction` in `document-review/api/document-actions.ts`), re-validating with the same zod schema |
| Form UI | `features/<f>/components/organisms/<Name>.tsx` built from `shared/ui/primitives` (`input`, `select`, `textarea`, `label`, `sheet`) |

Main forms:
- `document-review`: `CorrectionSheet` (`documentCorrectionSchema` in `model/schemas.ts`) — document type, department, action, due date, urgent, notes. Values are `UPPER_SNAKE_CASE` codes; selects show Spanish labels. Extracted fields (NIT, invoice number, total) are not editable today.
- `document-review`: discard with a mandatory reason (`ReviewActions`, plain `useState` + `discardDocumentAction`; no RHF yet).
- `settings`: supplier master CSV upload (`SupplierMasterUpload`). Editing extra holidays from the UI does not exist (they come from `TAC_EXTRA_HOLIDAYS`).
- `session`: `LoginForm` uses `useActionState` with `loginAction`.
- `ledger`: `LedgerSearch` (URL search params).

## Validation and errors

- Schema messages are Spanish strings in the zod schema today (`model/schemas.ts`); there is no `form-errors.ts`. Move them to `shared/i18n/es.ts` when a second form needs them.
- No frontend NIT validation exists (no `shared/lib/nit.ts`); the backend is the authority (`NIT_CHECK_DIGIT_INVALID`).
- API errors: the Server Action returns `ActionResult` `{ok: false, code}`; the form shows `toast.error(describeError(code))`. Map to `form.setError(field, ...)` when the error `detail` names a field (`VALIDATION_ERROR` `detail.errors[].field`).
- Submit button disabled while `isSubmitting`; show inline progress on the button only.

## Accessibility

- Every input has a visible `<label>`; errors linked with `aria-describedby`; focus moves to the first invalid field on submit.
- Touch-friendly rules for small screens: `mobile-forms-with-react-hook-form-and-zod-mobile`.

## Checklist

- RHF + zodResolver; schema in `model/schemas.ts`?
- Defaults from the proposal; codes as values, Spanish labels in the UI?
- Server error codes mapped to fields or form alert?
- Tests: schema valid/invalid cases and submit behavior (Jest + RTL)?
