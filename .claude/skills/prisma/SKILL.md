---
name: prisma
description: Persistence layer for Docket (folder name is historical — there is no Prisma). SQLAlchemy 2 repositories as hexagonal infrastructure adapters (SQLite on-prem, Postgres on Render), schema/migration guidance, transactional filing-number assignment, and the openpyxl Excel ledger adapter that must preserve the client's workbook format. Use for any database, repository, migration or Excel ledger work in backend/.
---

# Skill — Persistence: SQLAlchemy repositories + Excel ledger

> **The folder name `prisma` is historical.** Docket has no Prisma. This skill covers SQLAlchemy 2 and the openpyxl ledger adapter.

## Goal

Keep persistence inside infrastructure adapters, make the operational database the source of truth, and keep the client's Excel ledger byte-for-byte compatible in format.

## 1) Stores

| Store | Engine | Where | Purpose |
|---|---|---|---|
| Operational DB | SQLite (on-prem, file in `TAC_DATA_DIR`) / Postgres (Render) via `TAC_DATABASE_URL` | `shared/infrastructure/db.py` | Documents, proposals, ledger entries, audit events, outbox |
| Client ledger | `.xlsx` via openpyxl | `features/ledger/infrastructure/` | The workbook Martha already uses; Docket appends rows |
| Catalogs | CSV (supplier master, departments) | `features/catalogs/infrastructure/csv_catalogs.py` | Read-only input from the client ERP export |

Code must run on both SQLite and Postgres: no engine-specific SQL, no Postgres-only types.

## 2) Layer rules

| Layer | SQLAlchemy / openpyxl |
|---|---|
| domain | Forbidden. Domain models are Pydantic/dataclasses, not ORM classes |
| application | Forbidden. Depends on `Protocol` ports (`LedgerRepository`, `DocumentRepository`, `LedgerWorkbook`) |
| infrastructure | Allowed. ORM models (`*Row`) and adapters map rows <-> domain models |

## 3) SQLAlchemy conventions

- SQLAlchemy 2 typed style: `DeclarativeBase`, `Mapped[...]`, `mapped_column`, `select()`.
- ORM classes end in `Row` (`DocumentRow`, `LedgerEntryRow`, `AuditEventRow`) and live in the slice's `infrastructure/` (`orm.py`); shared `Base` in `shared/infrastructure/db.py`.
- Tables and columns `snake_case`. Enum columns store the `UPPER_SNAKE_CASE` string value (`String`, not native DB enums) so both engines behave the same.
- Index frequently filtered fields: `status`, `due_date`, `filing_number` (unique), `(supplier_nit_normalized, document_number_normalized)` for duplicate detection.
- Sessions come from a session factory injected by `container.py`; one unit of work per use case call; commit in the adapter or a unit-of-work helper, never in the domain.
- Avoid N+1: load related rows with `selectinload`/joins; never query inside a loop over results.
- List endpoints paginate (`limit`/`offset`) and filter in SQL, not in Python.

## 4) Filing numbers and duplicates

- Format `TAC-2026-ER-#####` built in `shared/domain/identifiers.py`; prefix from `TAC_FILING_PREFIX`.
- Next number = max(last number in DB, last number in the workbook) + 1, assigned **on approval**, inside one transaction with a row lock (`with_for_update()` on Postgres; SQLite serializes writes with `BEGIN IMMEDIATE`).
- Numbers are never reused: voiding marks the entry `VOIDED` with a note.
- Duplicate invoice = same normalized NIT + normalized document number already in the ledger (including rows that came from the original workbook).

## 5) Schema changes and migrations

- The schema is created from the ORM metadata on startup (`Base.metadata.create_all`) for the demo and tests.
- If a change would break existing data (rename/drop column), add an Alembic migration instead of relying on `create_all`, and ask before running it on a shared database.
- Never run destructive SQL (`DROP`, `TRUNCATE`, `DELETE` without `WHERE`) on Render or on-prem data without explicit approval.
- Tests use an in-memory SQLite (`sqlite+pysqlite:///:memory:`) or a temp file.

## 6) Excel ledger adapter (openpyxl) — HARD RULES

- Never write to `material/3-datos-del-cliente/libro-radicacion-2026.xlsx`. Bootstrap copies it into `TAC_DATA_DIR`; exports write a new file.
- Keep the 12 columns, header row, column widths, number/date formats, styles and every existing row untouched. Only append rows after the last used row, copying the style of the previous data row.
- Values written to the workbook are the client's Spanish values, mapped from English codes through `shared/infrastructure/client_vocabulary.py` (`Department.ACCOUNTS_PAYABLE` -> the client's label). No Spanish literals elsewhere in the adapter.
- Dates as real `date` cells with the existing number format, not strings.
- Reading: detect existing duplicates in the original workbook (e.g. the same invoice filed twice) and report them; do not "fix" the client's rows.
- Test: write to a temp copy, reopen with openpyxl, assert headers, formats and pre-existing rows are identical and new rows match the expected numbers.

## 7) Checklist

| # | Check |
|---|---|
| 1 | No SQLAlchemy/openpyxl imports in domain or application? |
| 2 | Works on SQLite and Postgres (no engine-specific SQL)? |
| 3 | Indexes for filter/lookup fields; unique filing number? |
| 4 | Filing number assigned on approval under a lock, never reused? |
| 5 | No N+1; lists paginated? |
| 6 | Workbook format and existing rows preserved; `material/` untouched? |
| 7 | Spanish values only through `client_vocabulary.py`? |
| 8 | Repository/adapter tests against a temp DB / temp workbook? |
