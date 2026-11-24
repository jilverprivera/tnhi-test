---
name: nomenclature
description: Enforces Python naming and file layout conventions for the Docket backend — snake_case modules per layer, PascalCase use cases/ports/adapters with role names, UPPER_SNAKE_CASE codes, English-only identifiers, and test naming. Use when naming or placing any backend file, class, function, code or test.
---

# Skill — Backend nomenclature (Python)

## Goal

From a name alone, infer **what** a file is, **which slice** and **which layer** it belongs to. Everything in English.

## Files (snake_case)

| Kind | Pattern | Example |
|---|---|---|
| Domain module | `features/<slice>/domain/<concept>.py` | `filing/domain/rules.py`, `filing/domain/outbox_composer.py`, `ledger/domain/filing_number.py` |
| Ports | `features/<slice>/application/ports.py` | `ledger/application/ports.py` |
| Use case | `features/<slice>/application/<verb>_<noun>.py` (related read-only queries may share a module: `queries.py`, `use_cases.py`) | `filing/application/approve_documents.py`, `ingestion/application/import_emails.py` |
| Adapter | `features/<slice>/infrastructure/<tech>_<noun>.py` | `ledger/infrastructure/excel_ledger.py`, `sql_ledger.py`, `catalogs/infrastructure/csv_catalogs.py`, `audit/infrastructure/sql_audit_log.py` |
| ORM rows | `shared/infrastructure/db.py` (all `*Row` classes today) | |
| Router / views | `features/<slice>/api/router.py` (request models inline), optional `views.py` | `filing/api/views.py` |
| Test | `tests/features/<slice>/test_<topic>.py` | `tests/features/filing/test_rules.py` |

## Classes and symbols

| Kind | Style | Example |
|---|---|---|
| Use case | `PascalCase` verb + noun, `__call__` | `ApproveDocuments`, `CorrectDocument`, `ImportEmails`, `ListDeadlines` |
| Port | `PascalCase` role noun (`Protocol`) | `LedgerRepository`, `CatalogSource`, `TextExtractor`, `AuditLog` |
| Adapter | technology prefix + port name | `SqlLedgerRepository`, `ExcelLedgerWorkbook`, `CsvCatalogs`, `PdfExtractor`, `TesseractOcr`, `ClaudeClassifier` |
| ORM row | `<Entity>Row` | `LedgerRow`, `AuditRow` |
| API request model | `<Thing>Request` (frontend raw response types are `<Thing>Response`) | `ApproveRequest`, `DiscardRequest` |
| Domain error | `<Problem>Error` (plain exception; the router maps it to a code) | `DocumentNotFoundError` -> `DOCUMENT_NOT_FOUND` |
| Enum | `PascalCase` class, `UPPER_SNAKE_CASE` members = values | `DocumentStatus.NEEDS_REVIEW` |
| Functions, variables | `snake_case` | `format_filing_number`, `due_date` |
| Booleans | `is_` / `has_` / `should_` | `is_business_day`, `is_fileable` |
| Constants | `UPPER_SNAKE_CASE` | `DIGITS = 5` (`ledger/domain/filing_number.py`) |
| Codes (reason, error, event) | `UPPER_SNAKE_CASE` strings | `EMAIL_ACCOUNT_MISMATCH`, `DOCUMENT_APPROVED` |

## Language

- Identifiers, docstrings, comments, log messages, test names: English.
- Domain terms map to English consistently: radicado -> `filing_number`, radicar -> `file`, dependencia -> `department`, maestro de proveedores -> `supplier master`, derecho de petición -> `petition`, oficio de ente de control -> `oversight notice`, viáticos -> `travel expense request`, libro de radicación -> `ledger`, días hábiles -> `business days`, vencimiento -> `due date`.
- Spanish appears only as data: regex keywords that detect Spanish text, client vocabulary values, Excel cells, outbox templates.

## Database

Tables plural `snake_case` (`ledger_entries`, `audit_events`); columns `snake_case`.

## Checklist

- File in the right slice/layer with a role-revealing name?
- Class name tells its role (use case verb, port noun, adapter tech prefix)?
- Codes `UPPER_SNAKE_CASE`; everything else English?
- Test file mirrors the module it tests?
