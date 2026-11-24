---
name: architecture-api
description: Enforces the Docket backend architecture — FastAPI vertical slices with hexagonal layers inside each slice (domain, application ports/use cases, infrastructure adapters, api routers), composition in container.py, and the read-only MCP server as a driving adapter. Use when creating or changing any backend endpoint, use case, port, adapter, rule or slice.
---

# Skill — Backend architecture (vertical slices + hexagonal)

## Goal

Keep business rules pure and testable, keep IO at the edges, and make each slice readable on its own.

## 1) Layout

```
backend/app/
  main.py                # FastAPI app, include routers, exception handlers
  container.py           # builds adapters and use cases from Settings; the only wiring place
  shared/
    config.py            # Settings (pydantic-settings, env prefix TAC_)
    domain/              # models.py, business_calendar.py, identifiers.py
    infrastructure/      # db.py (SQLAlchemy engine/session), client_vocabulary.py
  features/<slice>/
    domain/              # pure logic: rules, value objects, calculations
    application/         # ports.py (Protocols) + one module per use case
    infrastructure/      # adapters implementing ports
    api/                 # router.py + schemas.py (Pydantic request/response)
  mcp/server.py          # read-only MCP tools over ledger/deadlines use cases
```

Slices: `catalogs` (supplier master, departments), `ingestion` (.eml, text extraction, OCR), `classification` (type + fields), `filing` (rules -> Proposal, approve/correct, review queue), `ledger` (filing numbers, duplicates, Excel), `deadlines` (due dates, weekly report).

## 2) Dependency rule (HARD)

```
domain <- application <- infrastructure
                      <- api
```

| Layer | May import | Must not import |
|---|---|---|
| domain | stdlib, `pydantic`, `app.shared.domain` | FastAPI, SQLAlchemy, openpyxl, pdfplumber, pytesseract, anthropic, `app.shared.config` |
| application | its slice's domain, `app.shared.domain`, other slices' **application** use cases/ports | any `infrastructure` package |
| infrastructure | anything; implements ports | `api` |
| api | its slice's application + schemas | infrastructure (get use cases from the container) |

Cross-slice: `filing` may call `ledger.application.assign_filing_number.AssignFilingNumber`, never `ledger.infrastructure.*`.

## 3) Ports

Ports are `typing.Protocol` classes in `features/<slice>/application/ports.py`:

```python
class SupplierCatalog(Protocol):
    def find_by_nit(self, nit: str) -> Supplier | None: ...
```

Adapters implement them structurally (`CsvSupplierCatalog`, `SqlAlchemyLedgerRepository`, `OpenpyxlLedgerWorkbook`). Keep ports slim and per need, no god-repositories.

## 4) Use cases

One class per use case, one action, invoked with `__call__`, dependencies injected in `__init__`:

```python
class ApproveDocuments:
    def __init__(self, inbox: InboxRepository, ledger: LedgerRepository, workbook: LedgerWorkbook,
                 outbox: Outbox, audit: AuditLog, catalogs: CatalogSource, prefix: str) -> None: ...

    def __call__(self, ids: list[str], actor: str, allow_review: bool = True) -> list[InboxItem]: ...
```

- Returns domain models; routers map them to response schemas.
- Raises domain errors carrying an `UPPER_SNAKE_CASE` `code` (`DOCUMENT_NOT_FOUND`, `DOCUMENT_NEEDS_REVIEW`, `DECISION_INCOMPLETE`); never `HTTPException`.
- Orchestration of several steps (approve -> number -> ledger -> audit) is itself a use case in the owning slice; routers never call two use cases in a row.

## 5) Routers (driving adapters)

- Thin: parse input, call one use case, map output. No business logic, no DB access.
- URLs name the resource (all under `/api`): `POST /api/ingestion/upload`, `POST /api/ingestion/mailbox`, `GET /api/inbox?status=NEEDS_REVIEW`, `GET /api/inbox/summary`, `GET /api/inbox/{id}`, `GET /api/inbox/{id}/source`, `POST /api/inbox/{id}/correct`, `POST /api/inbox/{id}/discard`, `POST /api/inbox/approve` (`{"ids": [...]}`), `POST /api/inbox/approve-ready`, `GET /api/outbox`, `GET /api/audit`, `GET /api/ledger`, `GET /api/ledger/export`, `GET /api/ledger/duplicates`, `GET /api/deadlines`, `GET /api/deadlines/weekly-report`, `GET|PUT /api/catalogs/suppliers`, `GET /api/catalogs/departments`, `GET /api/health`, `GET /api/session`. Document ids look like `01.eml__0` (e-mail file + attachment position).
- JSON keys `snake_case`; enum values, statuses, reason codes, error codes `UPPER_SNAKE_CASE`.
- Envelope (`app/shared/infrastructure/http.py`): success `{"code": "DOCUMENTS_APPROVED", "data": ...}` via `ok(code, data)`; errors `{"code": "DOCUMENT_NOT_FOUND", "detail": {...}}` via `ApiError(status, code, **detail)`. Routers translate domain exceptions to `ApiError`; validation errors become `VALIDATION_ERROR` with `detail.errors[]`.
- Roles (Bearer token -> `Role`): `CLERK` (Martha: import, correct, approve, discard) and `COORDINATOR` (Dra. Herrera: read-only + deadlines/reports). Dependencies `AnyRole` / `ClerkRole`.

## 6) Rules engine (filing domain)

- One function per document type returning a `Decision` with `reasons[]` and `evidence[]`.
- Any blocking `Reason` makes the document `NEEDS_REVIEW`; the UI shows the reason code.
- Deadlines use `shared/domain/business_calendar.py` only.
- The LLM classifier is an optional adapter behind a port, off by default; its output goes through the same rules.

## 7) MCP server

`app/mcp/server.py` exposes read-only tools (`due_documents(start, end)`, `find_filing(query)`, `pending_review()`, `weekly_summary()`, `supplier_history(nit)`) by calling ledger/deadlines use cases from the container. No tool mutates state.

## 8) Pre-flight checklist

| # | Check |
|---|---|
| 1 | Code in the right slice and layer? |
| 2 | Domain free of framework/IO imports? |
| 3 | Cross-slice calls only through application use cases/ports? |
| 4 | One action per use case, `__call__`, dependencies injected? |
| 5 | Router thin; wiring only in `container.py`? |
| 6 | Codes `UPPER_SNAKE_CASE`, keys `snake_case`, everything in English? |
| 7 | Audit event for mutations (`audit-logging`)? |
| 8 | Tests per `testing`; golden test still 100 %? |
| 9 | Feature docs updated in `docs/en/features/` and `docs/es/features/`? |
