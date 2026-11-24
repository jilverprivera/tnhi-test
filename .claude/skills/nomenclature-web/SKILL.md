---
name: nomenclature-web
description: Enforces naming conventions for Docket frontend files, components, hooks, api functions, model types, i18n keys and tests (features + shared + atomic design, English identifiers). Use when naming, renaming or placing any file or symbol in frontend/.
---

# Skill — Frontend nomenclature

## Core rules

- All identifiers in English. Spanish only as i18n values in `shared/i18n/`.
- One component per file (see `ui-structure-web`).
- Folder names lowercase kebab-case (`document-review`, `__tests__`).

## Files

| Kind | Pattern | Example |
|---|---|---|
| Primitive (shadcn) | `kebab-case.tsx` in `shared/ui/primitives/` | `button.tsx`, `sheet.tsx` |
| Atom / molecule / organism / template | `PascalCase.tsx` | `StatusBadge.tsx`, `InboxTable.tsx`, `InboxTemplate.tsx` |
| Skeleton | `<Name>Skeleton.tsx` next to its component | `InboxTableSkeleton.tsx` |
| Hook | `use<Name>.ts` in `hooks/` | `useApproveDocument.ts`, `useInboxFilters.ts` |
| API function module | `kebab-case.ts` in `api/` | `api/approve-document.ts` |
| Model | `model/types.ts`, `model/mappers.ts`, `model/schemas.ts` (zod) | |
| i18n | `shared/i18n/<namespace>.ts` | `shared/i18n/reason-codes.ts` |
| Unit/component test | `__tests__/<Name>.test.tsx` | `features/inbox/__tests__/InboxTable.test.tsx` |
| E2E spec | `frontend/e2e/<flow>.spec.ts` | `e2e/batch-approve.spec.ts` |

## Symbols

| Kind | Style | Example |
|---|---|---|
| Components | `PascalCase` | `DocumentFieldsPanel` |
| Hooks | `useCamelCase` | `useDocumentCorrectionForm` |
| API functions | verb + noun, camelCase | `fetchInbox`, `approveDocument`, `correctDocument` |
| API types (raw) | `<Thing>Response` / `<Thing>Request`, keys `snake_case` | `DocumentResponse` |
| View models | `<Thing>View`, keys `camelCase` | `DocumentView` |
| Mappers | `to<Thing>View` | `toDocumentView` |
| Zod schemas | `<name>Schema` | `documentCorrectionSchema` |
| Code unions | `PascalCase` type, `UPPER_SNAKE_CASE` members | `type ReasonCode = "INVOICE_ACCOUNT_MISMATCH" | ...` |
| Constants | `UPPER_SNAKE_CASE` | `INBOX_PAGE_SIZE` |
| Booleans | `is` / `has` / `should` | `isUrgent`, `hasReasons` |

## Imports

- Use the `@/` alias for anything outside the current folder.
- Routes import feature barrels (`@/features/ledger`); features import shared through `@/shared/ui/...`, `@/shared/lib/...`, `@/shared/i18n`.
- No compatibility re-export files, no `misc.ts` / `helpers2.ts`.

## Checklist

- Name reveals kind and layer? Component file `PascalCase.tsx` in the right layer?
- Hooks start with `use`; API functions are verb + noun?
- Raw API types keep `snake_case`; view models `camelCase`?
- Tests in `__tests__/` and named after the unit?
