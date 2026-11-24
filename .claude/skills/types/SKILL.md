---
name: types
description: Defines where Docket's types live and how the API contract crosses from the FastAPI backend to the Next.js frontend — domain enums in shared/domain/models.py, Pydantic request models in each slice's api/router.py, dict response views wrapped in an envelope, UPPER_SNAKE_CASE codes, snake_case keys, raw `<Thing>Response` types in web/src/shared/lib/api-types.ts and per-feature view models plus mappers. Use when adding or changing an enum, reason/error code, endpoint payload, or a frontend type that mirrors the API.
---

# Skill — Types and the API contract

There is no shared types package. The backend owns the contract; the frontend mirrors it per feature.

## Backend

| Kind | Lives in |
|---|---|
| Cross-slice enums (`DocumentType`, `Department`, `Action`, `DocumentStatus`) and core models (`Decision`, `Reason`, `Evidence`, `Document`, `Proposal`, `LedgerEntry`) | `app/shared/domain/models.py` |
| Slice-only domain types | `features/<slice>/domain/` |
| Ports | `features/<slice>/application/ports.py` (`Protocol`) |
| Request models | Pydantic `*Request` classes in the slice's `api/router.py` (`ApproveRequest`, `DiscardRequest` in `filing/api/router.py`); the correction payload is `Correction` in `filing/application/correct_document.py`. There is no `api/schemas.py` |
| Response shapes | Plain dicts built by view functions (`filing/api/views.py`: `inbox_item_view`) or `model_dump(mode="json")`, wrapped in `Envelope` (`{"code", "data"}`) from `shared/infrastructure/http.py`; paginated lists return `Page` (`{items, total, limit, offset}`, `shared/domain/pagination.py`), mirrored as `PageResponse<T>` on the web |
| ORM rows | `DocumentRow`, `LedgerRow`, `AuditRow`, `OutboxRow` in `app/shared/infrastructure/db.py` — never returned by routers |

Rules:

- Enums are `StrEnum` whose values equal their names in `UPPER_SNAKE_CASE`.
- Reason codes (the `_reason("...")` calls in `filing/domain/rules.py`, e.g. `DOCUMENT_UNREADABLE`, `LOW_OCR_CONFIDENCE`, `SUPPLIER_NOT_REGISTERED`, `EMAIL_ACCOUNT_MISMATCH`, `INVOICE_DUPLICATE`, `OVERSIGHT_TERM_NOT_FOUND`, plus `REVIEWED_BY_HUMAN` from `correct_document.py`) and error codes (`DOCUMENT_NOT_FOUND`, `DOCUMENT_NEEDS_REVIEW`, `DOCUMENT_ALREADY_CLOSED`, `DECISION_INCOMPLETE`, `HOLD_REQUIRES_ESCALATION`, `NOT_A_HOLD`, `IMPORT_JOB_NOT_FOUND`, `IMPORT_FAILED`, `RECORD_NOT_FOUND`, `RETENTION_NOT_EXPIRED`, `DISPOSITION_NOT_ALLOWED`, `DISPOSAL_RECORD_REQUIRED`, `IDENTIFIER_TOO_SHORT`) are stable strings; adding one means adding its Spanish label in the frontend and documenting it in the feature docs.
- JSON keys `snake_case`; dates ISO 8601 (`2026-11-23`); datetimes with offset.
- Never expose Spanish client values in the API; translation to the ledger happens in `client_vocabulary.py`, translation to the UI in the frontend.
- FastAPI publishes `/openapi.json`, but responses are untyped dict envelopes, so it documents paths and request models only; `web/src/shared/lib/api-types.ts` is the hand-maintained mirror of the response shapes.

## Frontend

| Kind | Lives in |
|---|---|
| Raw API types (`snake_case`), named `<Thing>Response` (`InboxItemResponse`, `DecisionResponse`, `ReasonResponse`, `LedgerEntryResponse`, `DeadlineResponse`, `AuditEventResponse`, ...), plus `Envelope<T>`, `ErrorResponse` and code unions (`DocumentType`, `Department`, `Action`, `DocumentStatus`, `OutboxKind`, ...) | `src/shared/lib/api-types.ts` |
| Feature view models (`camelCase`, `*View`: `InboxItemView`, `DocumentDetailView`, ...) | `src/features/<feature>/model/types.ts` |
| Mappers `<Thing>Response` -> `*View` | `src/features/<feature>/model/mappers.ts` |
| Spanish labels for codes | `src/shared/i18n/` (see `translation-web`) |
| Component props | next to the component (`Name.types.ts` or inline) |

Rules:

- Mirror codes as string-literal unions, usually derived from a `const` array: `export const DOCUMENT_STATUSES = ["READY", "NEEDS_REVIEW", "APPROVED", "DISCARDED"] as const;`. Reason codes are plain `string` on the frontend; their labels live in `reasonLabel` (`shared/i18n/es.ts`), falling back to the raw code.
- Keep `snake_case` in raw API types; mappers convert to `camelCase` view models. Components consume view models only.
- Never redefine a type that exists in `shared/lib/api-types.ts`; never import another feature's `model/`.
- No `any`; unknown codes from the API fall back to the raw code (`describeReason` in `shared/i18n/es.ts`).
- `shared/lib/api-types.ts` is hand-written (no `openapi-typescript` generation today).

## Workflow for a new code or field

1. Add it to the backend enum / request model / view; test the router output.
2. Update `shared/lib/api-types.ts` (raw `<Thing>Response`), and the feature's `model/types.ts` view model and mapper if the UI uses it.
3. Add the Spanish label in `shared/i18n/`.
4. Document the code in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`.
