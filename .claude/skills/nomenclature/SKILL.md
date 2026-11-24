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
| Domain module | `features/<slice>/domain/<concept>.py` | `filing/domain/invoice_rules.py` |
| Ports | `features/<slice>/application/ports.py` | `ledger/application/ports.py` |
| Use case | `features/<slice>/application/<verb>_<noun>.py` | `filing/application/approve_document.py` |
| Adapter | `features/<slice>/infrastructure/<tech>_<noun>.py` | `ledger/infrastructure/openpyxl_ledger_workbook.py`, `sqlalchemy_ledger_repository.py`, `csv_catalogs.py` |
| ORM rows | `features/<slice>/infrastructure/orm.py` | |
| Router / schemas | `features/<slice>/api/router.py`, `schemas.py` | |
| Test | `tests/features/<slice>/test_<module>.py` | `tests/features/filing/test_invoice_rules.py` |

## Classes and symbols

| Kind | Style | Example |
|---|---|---|
| Use case | `PascalCase` verb + noun, `__call__` | `ApproveDocument`, `AssignFilingNumber`, `ListDueDocuments` |
| Port | `PascalCase` role noun (`Protocol`) | `LedgerRepository`, `SupplierCatalog`, `TextExtractor` |
| Adapter | technology prefix + port name | `SqlAlchemyLedgerRepository`, `OpenpyxlLedgerWorkbook`, `TesseractOcrExtractor`, `ClaudeClassifier` |
| ORM row | `<Entity>Row` | `LedgerEntryRow` |
| API schema | `<Thing>Request` / `<Thing>Response` | `CorrectDocumentRequest` |
| Domain error | `<Problem>Error` with `code` | `DocumentNotFoundError(code="DOCUMENT_NOT_FOUND")` |
| Enum | `PascalCase` class, `UPPER_SNAKE_CASE` members = values | `DocumentStatus.NEEDS_REVIEW` |
| Functions, variables | `snake_case` | `count_business_days`, `due_date` |
| Booleans | `is_` / `has_` / `should_` | `is_duplicate`, `has_purchase_order` |
| Constants | `UPPER_SNAKE_CASE` | `FILING_NUMBER_WIDTH = 5` |
| Codes (reason, error, event) | `UPPER_SNAKE_CASE` strings | `INVOICE_ACCOUNT_MISMATCH`, `DOCUMENT_APPROVED` |

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
