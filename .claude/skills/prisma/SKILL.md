---
name: prisma
description: Persistence layer for Docket (folder name is historical — there is no Prisma). SQLAlchemy 2 repositories as hexagonal infrastructure adapters (SQLite on-prem, Postgres on Render), schema/migration guidance, transactional filing-number assignment, and the openpyxl Excel ledger adapter that must preserve the client's workbook format. Use for any database, repository, migration or Excel ledger work in api/.
---

# Skill — Persistence: SQLAlchemy repositories + Excel ledger

> **The folder name `prisma` is historical.** Docket has no Prisma. This skill covers SQLAlchemy 2 and the openpyxl ledger adapter.

## Goal

Keep persistence inside infrastructure adapters, make the operational database the source of truth, and keep the client's Excel ledger byte-for-byte compatible in format.

## 1) Stores

| Store | Engine | Where | Purpose |
|---|---|---|---|
| Operational DB | SQLite (on-prem, file in `TAC_DATA_DIR`) / Postgres (Render) via `TAC_DATABASE_URL` | `shared/infrastructure/db.py` | Documents, proposals, ledger entries, audit events, outbox |
| Client ledger | `.xlsx` via openpyxl | `features/ledger/infrastructure/excel_ledger.py` (`ExcelLedgerWorkbook`) | The workbook Martha already uses. Read once at seed (`SeedLedger`, only when the DB ledger is empty); afterwards kept in step both ways by `SyncLedger` (`read_table` / `write_table`, three-way merge per cell against the bases in `ledger_sync_base`, `SqlSyncStore`) on approvals, hold resolutions, disposals, exports and every `TAC_LEDGER_SYNC_SECONDS` |
| Catalogs | CSV (supplier master, departments) | `features/catalogs/infrastructure/csv_catalogs.py` | Read-only input from the client ERP export |

Code must run on both SQLite and Postgres: no engine-specific SQL, no Postgres-only types.

## 2) Layer rules

| Layer | SQLAlchemy / openpyxl |
|---|---|
| domain | Forbidden. Domain models are Pydantic/dataclasses, not ORM classes |
| application | Forbidden. Depends on `Protocol` ports (`LedgerRepository`, `LedgerWorkbook`, `InboxRepository`, `Outbox`, `AuditLog`) |
| infrastructure | Allowed. ORM models (`*Row`) and adapters map rows <-> domain models |

## 3) SQLAlchemy conventions

- SQLAlchemy 2 typed style: `DeclarativeBase`, `Mapped[...]`, `mapped_column`, `select()`.
- ORM classes end in `Row` (`DocumentRow`, `LedgerRow`, `AuditRow`, `OutboxRow`, `ImportJobRow` / `ImportJobFileRow` for the import queue) and today all live with the shared `Base` in `shared/infrastructure/db.py`; repositories that map them live in each slice's `infrastructure/` (`SqlLedgerRepository`, `SqlInboxRepository`, `SqlOutbox`, `SqlAuditLog`, `SqlJobQueue`). Lists that can grow page in SQL (`SqlInboxRepository.page`: `LIMIT/OFFSET` + `COUNT`) and return `Page[T]` (`shared/domain/pagination.py`); `purge_content` empties text and original file for retention disposal.
- Tables and columns `snake_case`. Enum columns store the `UPPER_SNAKE_CASE` string value (`String`, not native DB enums) so both engines behave the same.
- Index frequently filtered fields: `documents.status`, `ledger_entries.due_date`, `ledger_entries.sequence` (unique), `documents.filing_number` (unique), `ledger_entries.nit_key` / `document_number_key` for duplicate detection.
- Sessions come from a session factory injected by `container.py`; each adapter method opens and commits its own session (`with sessions.begin()`), never in the domain. There is no cross-repository unit of work today (known gap).
- Avoid N+1: load related rows with `selectinload`/joins; never query inside a loop over results.
- Known gap / to do: list endpoints (`/api/inbox`, `/api/ledger`) do not paginate today, and some filtering happens in Python (`ListLedger`). New list endpoints should paginate (`limit`/`offset`) and filter in SQL.

## 4) Filing numbers and duplicates

- Format `TAC-2026-ER-#####` built by `format_filing_number` / parsed by `parse_sequence` in `features/ledger/domain/filing_number.py`; prefix from `TAC_FILING_PREFIX`.
- Next number = `LedgerRepository.last_sequence() + 1` (`MAX(ledger_entries.sequence)` in the DB only), assigned **on approval** in `ApproveDocuments`. The workbook is not consulted at that point: its historical rows were loaded into the DB once by `SeedLedger`.
- Concurrency: an in-process `threading.Lock` (`_SEQUENCE_LOCK`) serializes assignment, and the unique constraints on `ledger_entries.sequence` / `documents.filing_number` are the last line of defense. Known gap: this only protects a single process; a multi-process/multi-instance deployment would need `SELECT ... FOR UPDATE` or a DB sequence.
- Numbers are never reused. There is no `VOIDED` status or voiding flow today (future work: it would mark the entry, never delete or renumber it).
- Duplicate invoice = same `invoice_key` (normalized NIT + normalized document number, `features/ledger/domain/duplicates.py`) already in the ledger (including rows seeded from the original workbook).

## 5) Schema changes and migrations

- The schema is created from the ORM metadata on startup (`Base.metadata.create_all`) for the demo and tests.
- If a change would break existing data (rename/drop column), add an Alembic migration instead of relying on `create_all`, and ask before running it on a shared database.
- Never run destructive SQL (`DROP`, `TRUNCATE`, `DELETE` without `WHERE`) on Render or on-prem data without explicit approval.
- Tests use an in-memory SQLite (`sqlite+pysqlite:///:memory:`) or a temp file.

## 6) Excel ledger adapter (openpyxl) — HARD RULES

- Never write to `material/3-datos-del-cliente/libro-radicacion-2026.xlsx`. `ExcelLedgerWorkbook` copies it into `TAC_DATA_DIR` (`libro-radicacion-2026.xlsx`) on first use and only writes that working copy; `GET /api/ledger/export` returns rendered bytes.
- Keep the 12 columns, header row, column widths, number/date formats and styles untouched. New rows are appended after the last used row, copying the style of the previous data row; existing rows change only in the cells Docket changed (people win on conflict). Never write while Excel's `~$` lock file exists (`WorkbookLockedError`) or if the file version changed since it was read (`WorkbookChangedError`); replace the file atomically.
- Values written to the workbook are the client's Spanish values, mapped from English codes through `shared/infrastructure/client_vocabulary.py` (`Department.ACCOUNTS_PAYABLE` -> the client's label). No Spanish literals elsewhere in the adapter.
- Dates exactly as the client's book stores them: ISO text (`"2026-11-04"`, cell type string), not `date` cells — verified in `material/3-datos-del-cliente/libro-radicacion-2026.xlsx`. "Valor total" stays numeric. When reading, accept both (people may type real dates): `normalize_cell` turns them into ISO text.
- Reading: detect existing duplicates in the original workbook (e.g. the same invoice filed twice) and report them (`FindLedgerDuplicates`, `GET /api/ledger/duplicates`); do not "fix" the client's rows.
- Test: write to a temp copy, reopen with openpyxl, assert headers, formats and pre-existing rows are identical and new rows match the expected numbers.

## 7) Checklist

| # | Check |
|---|---|
| 1 | No SQLAlchemy/openpyxl imports in domain or application? |
| 2 | Works on SQLite and Postgres (no engine-specific SQL)? |
| 3 | Indexes for filter/lookup fields; unique filing number? |
| 4 | Filing number assigned on approval under the sequence lock + unique constraint, never reused? |
| 5 | No N+1; lists paginated? |
| 6 | Workbook format and existing rows preserved; `material/` untouched? |
| 7 | Spanish values only through `client_vocabulary.py`? |
| 8 | Repository/adapter tests against a temp DB / temp workbook? |
