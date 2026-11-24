---
name: types
description: Defines where Docket's types live and how the API contract crosses from the FastAPI backend to the Next.js frontend — domain enums in shared/domain/models.py, Pydantic request/response schemas per slice api/, UPPER_SNAKE_CASE codes, snake_case keys, and frontend feature model/ types plus mappers. Use when adding or changing an enum, reason/error code, endpoint payload, or a frontend type that mirrors the API.
---

# Skill — Types and the API contract

There is no shared types package. The backend owns the contract; the frontend mirrors it per feature.

## Backend

| Kind | Lives in |
|---|---|
| Cross-slice enums (`DocumentType`, `Department`, `Action`, `DocumentStatus`) and core models (`Decision`, `Reason`, `Evidence`, `Document`, `Proposal`, `LedgerEntry`) | `app/shared/domain/models.py` |
| Slice-only domain types | `features/<slice>/domain/` |
| Ports | `features/<slice>/application/ports.py` (`Protocol`) |
| Request/response schemas | `features/<slice>/api/schemas.py` (Pydantic, `*Request` / `*Response`) |
| ORM rows | `features/<slice>/infrastructure/orm.py` (`*Row`) — never returned by routers |

Rules:

- Enums are `StrEnum` whose values equal their names in `UPPER_SNAKE_CASE`.
- Reason codes (`INVOICE_ACCOUNT_MISMATCH`, `SUPPLIER_NOT_FOUND`, `LOW_OCR_CONFIDENCE`, `DEADLINE_NOT_READABLE`) and error codes (`DOCUMENT_NOT_FOUND`) are stable strings; adding one means adding its Spanish label in the frontend and documenting it in the feature docs.
- JSON keys `snake_case`; dates ISO 8601 (`2026-11-23`); datetimes with offset.
- Never expose Spanish client values in the API; translation to the ledger happens in `client_vocabulary.py`, translation to the UI in the frontend.
- The OpenAPI schema (`/openapi.json`) is the published contract.

## Frontend

| Kind | Lives in |
|---|---|
| API response/request types for a feature | `src/features/<feature>/model/types.ts` |
| Mappers API -> view model | `src/features/<feature>/model/mappers.ts` |
| Code unions used by several features (`DocumentStatus`, `ReasonCode`) | `src/shared/lib/api-types.ts` |
| Spanish labels for codes | `src/shared/i18n/` (see `translation-web`) |
| Component props | next to the component (`Name.types.ts` or inline) |

Rules:

- Mirror codes as string-literal unions: `type DocumentStatus = "READY" | "NEEDS_REVIEW" | "APPROVED" | "DISCARDED";`
- Keep `snake_case` in raw API types; mappers convert to `camelCase` view models. Components consume view models only.
- Never redefine a type that exists in `shared/lib/api-types.ts`; never import another feature's `model/`.
- No `any`; unknown codes from the API map to a safe fallback label and are logged.
- Optionally generate `shared/lib/api-types.ts` from `/openapi.json` with `openapi-typescript`; generated files are not hand-edited.

## Workflow for a new code or field

1. Add it to the backend enum/schema; test the router output.
2. Update `features/<feature>/model/types.ts` (or `shared/lib/api-types.ts`) and the mapper.
3. Add the Spanish label in `shared/i18n/`.
4. Document the code in `docs/en/features/<slug>.md` and `docs/es/features/<slug>.md`.
