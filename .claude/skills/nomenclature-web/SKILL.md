---
name: nomenclature-web
description: Enforces naming conventions for Docket frontend files, components, hooks, api functions, model types, i18n keys and tests (features + shared + atomic design, English identifiers). Use when naming, renaming or placing any file or symbol in web/.
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
| Atom / molecule / organism / template | `PascalCase.tsx` | `StatusBadge.tsx`, `InboxList.tsx`, `InboxTemplate.tsx` |
| Skeleton | `<Name>Skeleton.tsx` next to its component | `templates/InboxSkeleton.tsx` |
| Hook | `use<Name>.ts` in `hooks/` (none exist yet) | `useInboxFilters.ts` |
| API function module | `<feature>-queries.ts` (server reads) / `<feature>-actions.ts` (Server Actions) in `api/` | `api/inbox-queries.ts`, `api/document-actions.ts` |
| Model | `model/types.ts`, `model/mappers.ts`, `model/schemas.ts` (zod) | |
| i18n | `shared/i18n/<locale>.ts` | `shared/i18n/es.ts` |
| Unit/component test | `__tests__/<name>.test.ts(x)` | `features/inbox/__tests__/mappers.test.ts` |
| E2E spec | `web/e2e/<flow>.spec.ts` | `e2e/filing-flow.spec.ts` |

## Symbols

| Kind | Style | Example |
|---|---|---|
| Components | `PascalCase` | `CorrectionSheet`, `ReviewActions` |
| Hooks | `useCamelCase` | `useInboxFilters` |
| API functions | queries `fetch<Thing>`; Server Actions verb + noun + `Action` | `fetchInbox`, `fetchDocument`, `approveDocumentAction`, `correctDocumentAction` |
| API types (raw) | `<Thing>Response`, keys `snake_case`, in `shared/lib/api-types.ts` | `InboxItemResponse`, `DecisionResponse` |
| View models | `<Thing>View`, keys `camelCase` | `InboxItemView`, `DocumentDetailView` |
| Mappers | `to<Thing>View` | `toInboxItemView`, `toDocumentDetailView` |
| Zod schemas | `<name>Schema` | `documentCorrectionSchema` |
| Code unions | `PascalCase` type, `UPPER_SNAKE_CASE` members | `type OutboxKind = "FORWARD_TO_DEPARTMENT" | ...` |
| Constants | `UPPER_SNAKE_CASE` | `INBOX_FILTERS`, `DOCUMENT_STATUSES` |
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
