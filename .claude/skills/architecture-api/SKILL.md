---
name: architecture-api
description: Enforces the Docket backend architecture — FastAPI vertical slices with hexagonal layers inside each slice (domain, application ports/use cases, infrastructure adapters, api routers), composition in container.py, and the read-only MCP server as a driving adapter. Use when creating or changing any backend endpoint, use case, port, adapter, rule or slice.
---

# Skill — Backend architecture (vertical slices + hexagonal)

## Goal

Keep business rules pure and testable, keep IO at the edges, and make each slice readable on its own.

## 1) Layout

```
api/app/
  main.py                # FastAPI app, include routers, exception handlers
  container.py           # builds adapters and use cases from Settings; the only wiring place
  shared/
    config.py            # Settings (pydantic-settings, env prefix TAC_)
    domain/              # models.py, business_calendar.py, identifiers.py, pagination.py (Page[T], PageRequest), privacy.py (mask_personal_data, mask_identifier)
    infrastructure/      # db.py (SQLAlchemy Base, *Row models, engine/session), http.py (envelope, ApiError, roles), client_vocabulary.py, observability.py (metrics, JSON logs, MeteredAuditLog)
  features/<slice>/
    domain/              # pure logic: rules, value objects, calculations
    application/         # ports.py (Protocols) + one module per use case
    infrastructure/      # adapters implementing ports
    api/                 # router.py (Pydantic *Request models inline) + optional views.py (dict response views)
  mcp/server.py          # read-only MCP tools over ledger/deadlines use cases
```

Slices: `catalogs` (supplier master, departments), `ingestion` (.eml, text extraction, OCR; import queue: `EnqueueImport` / `ProcessNextImport`, `JobQueue` port, `SqlJobQueue`, `ImportWorker` thread), `classification` (type + fields, optional Claude adapter), `filing` (rules -> Proposal, approve/correct/discard, `EscalateHold` for suspected fraud (never approved: `HOLD_REQUIRES_ESCALATION`), review queue, outbox, held-invoice verification: `VerifyHold` use case in `application/verify_hold.py`, `ListHeldInvoices` in `application/queries.py`, `api/verifications_router.py` with `GET /api/verifications` (any role) and `POST /api/verifications/{id}/release|reject` (`CoordinatorRole`)), `ledger` (filing-number format, duplicates, SQL ledger, Excel; two-way sync with the shared Excel: `SyncLedger`, `domain/sync.py` `merge_row`), `deadlines` (due dates, weekly report), `audit` (append-only trail, `GET /api/audit`), `records` (retention schedule Ley 594 de 2000: `GetRetentionSchedule`, `ListRetention`, `DisposeRecord`), `privacy` (habeas data Ley 1581 de 2012: `INVENTORY`, `FindDataSubject`). List endpoints paginate with `PageRequest` (`limit` default 50, clamped to `MAX_LIMIT` 200) and return `Page` (`{items, total, limit, offset}`).

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
| api | its slice's application + `app.shared.infrastructure.http` | other infrastructure (get use cases from the container) |

Cross-slice: `filing` depends on `ledger.application.ports` (`LedgerRepository`, `LedgerWorkbook`) and `ledger.domain.filing_number.format_filing_number`, never `ledger.infrastructure.*` (adapters are injected by `container.py`).

## 3) Ports

Ports are `typing.Protocol` classes in `features/<slice>/application/ports.py`:

```python
class CatalogSource(Protocol):
    def supplier_master(self) -> SupplierMaster: ...
    def departments(self) -> dict[Department, DepartmentInfo]: ...
```

Adapters implement them structurally (`CsvCatalogs`, `SqlLedgerRepository`, `ExcelLedgerWorkbook`, `SqlInboxRepository`, `SqlOutbox`, `SqlAuditLog`, `ClaudeClassifier` / `DisabledClassifier`). Keep ports slim and per need, no god-repositories.

## 4) Use cases

One class per use case, one action, invoked with `__call__`, dependencies injected in `__init__`:

```python
class ApproveDocuments:
    def __init__(self, inbox: InboxRepository, ledger: LedgerRepository, workbook: LedgerWorkbook,
                 outbox: Outbox, audit: AuditLog, catalogs: CatalogSource, prefix: str) -> None: ...

    def __call__(self, ids: list[str], actor: str, allow_review: bool = True) -> list[InboxItem]: ...
```

- Returns domain models; routers map them to dicts (`model_dump(mode="json")` or a view function such as `inbox_item_view`).
- Raises plain domain exceptions (`DocumentNotFoundError`, `DocumentNotApprovableError`, `DecisionIncompleteError`, `DocumentAlreadyClosedError`, `HoldNotPendingError`, `VerificationNoteRequiredError`); never `HTTPException`. The router maps each one to an `UPPER_SNAKE_CASE` error code (`DOCUMENT_NOT_FOUND`, `DOCUMENT_NEEDS_REVIEW`, `DECISION_INCOMPLETE`, `DOCUMENT_ALREADY_CLOSED`, `HOLD_NOT_PENDING`, `VERIFICATION_NOTE_REQUIRED`).
- Orchestration of several steps (approve -> number -> ledger -> outbox -> audit) is itself a use case in the owning slice; routers should not call two use cases in a row. Known exception: `PUT /api/catalogs/suppliers` calls the catalog adapter and `audit.record` directly from the router (to do: move into a use case).

## 5) Routers (driving adapters)

- Thin: parse input, call one use case, map output. No business logic, no DB access.
- URLs name the resource (all under `/api`): `POST /api/ingestion/upload`, `POST /api/ingestion/mailbox`, `POST /api/ingestion/jobs/mailbox|upload` (202 `IMPORT_QUEUED`), `GET /api/ingestion/jobs`, `GET /api/ingestion/jobs/{id}`, `GET /api/inbox?status=NEEDS_REVIEW&status=READY&limit=50&offset=0`, `POST /api/inbox/{id}/escalate`, `GET /api/inbox/summary`, `GET /api/inbox/{id}`, `GET /api/inbox/{id}/source`, `POST /api/inbox/{id}/correct`, `POST /api/inbox/{id}/discard`, `POST /api/inbox/approve` (`{"ids": [...]}`), `POST /api/inbox/approve-ready`, `GET /api/outbox`, `GET /api/audit`, `GET /api/ledger`, `GET /api/ledger/export`, `GET|POST /api/ledger/sync`, `GET /api/ledger/duplicates`, `GET /api/deadlines`, `GET /api/deadlines/weekly-report`, `GET|PUT /api/catalogs/suppliers`, `GET /api/catalogs/departments`, `GET /api/health`, `GET /api/ready`, `GET /metrics`, `GET /api/session`, `GET /api/retention/schedule`, `GET /api/retention`, `POST /api/retention/{filing_number}/dispose`, `GET /api/privacy/inventory`, `POST /api/privacy/subject-requests` (identifier in the body, never the URL). Document ids look like `01.eml__0` (e-mail file + attachment position).
- JSON keys `snake_case`; enum values, statuses, reason codes, error codes `UPPER_SNAKE_CASE`.
- Envelope (`app/shared/infrastructure/http.py`): success `{"code": "DOCUMENTS_APPROVED", "data": ...}` via `ok(code, data)`; errors `{"code": "DOCUMENT_NOT_FOUND", "detail": {...}}` via `ApiError(status, code, **detail)`. Routers translate domain exceptions to `ApiError`; validation errors become `VALIDATION_ERROR` with `detail.errors[]`.
- Roles (Bearer token -> `Role`): `CLERK` (Martha: import, correct, approve, discard) and `COORDINATOR` (Dra. Herrera: read-only + deadlines/reports, resolves held invoices, disposes of records, runs data subject lookups). Dependencies `AnyRole` / `ClerkRole` / `CoordinatorRole`.

## 6) Rules engine (filing domain)

- One function per document type returning a `Decision` with `reasons[]` and `evidence[]`.
- Any blocking `Reason` makes the document `NEEDS_REVIEW`; the UI shows the reason code.
- Deadlines use `shared/domain/business_calendar.py` only.
- The LLM classifier is an optional adapter behind a port, off by default; its output goes through the same rules.

## 7) MCP server

`app/mcp/server.py` (FastMCP) exposes read-only tools (`deadlines_this_week()`, `weekly_report()`, `list_deadlines(start, end)`, `search_ledger(...)`, `pending_review()`, `held_invoices()`, `inbox_summary()`) plus the resource `docket://week`, by calling deadlines/ledger/inbox use cases from the container. No tool mutates state. Default transport is stdio; `--http` serves streamable HTTP on port 8001, bound to `127.0.0.1` unless `TAC_MCP_HOST` is set.

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
