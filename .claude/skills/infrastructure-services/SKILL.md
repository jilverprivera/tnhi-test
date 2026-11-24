---
name: infrastructure-services
description: Rules for Docket's external integrations as hexagonal adapters — settings via TAC_ env vars, .eml reading, PDF text and local Tesseract OCR, simulated outbox (no real e-mail sending), CSV catalogs, and the optional Claude classifier (off by default, masked data). Use when adding or changing any adapter, environment variable or external dependency in backend/.
---

# Skill — Infrastructure services (adapters)

## Goal

Every external capability is an adapter behind a port, configured from one place, replaceable in tests by a fake.

## 1) Configuration — single source of truth (HARD RULE)

- All configuration comes from `app/shared/config.py` (`Settings`, pydantic-settings, `env_prefix="TAC_"`).
- Never read `os.environ` / `os.getenv` anywhere else. Adapters receive values from `container.py`.
- New variable: add a typed field with a safe default to `Settings` and document it in `.env.example`.
- Secrets (`TAC_ANTHROPIC_API_KEY`, `TAC_DATABASE_URL` with credentials) only from the environment; never commit them.

## 2) E-mail input (`ingestion`)

- `.eml` parsing with stdlib `email` + `policy.default` in `ingestion/infrastructure/eml_reader.py`.
- Each useful attachment is a document; the body is a document when no useful attachment exists. Keep the original `.eml` as evidence.
- Dates normalized to `America/Bogota` (-05:00).
- Real mailbox integration (Microsoft Graph / Gmail API) is future work; it would be another adapter for the same port.

## 3) Text extraction and OCR

- Native PDF: `pdfplumber`. Scanned PDF/image: render with `pypdfium2`, OCR with `pytesseract` (`lang="spa"`), returning text **and** a confidence score.
- OCR is local; no document leaves the server. The Docker image installs `tesseract-ocr` and `tesseract-ocr-spa`.
- Low OCR confidence (< `TAC_MIN_OCR_CONFIDENCE`) yields reason `LOW_OCR_CONFIDENCE`. Unsupported formats yield `UNSUPPORTED_FORMAT`. Both are blocking.
- Extractors implement one `TextExtractor` port and are selected by MIME type.

## 4) Outbox (simulated sending)

- Docket **never sends e-mail**. Forward/return/reply/alert messages are generated as `.eml` into the outbox (`GET /outbox`) for download and review.
- Messages are built from templates with the client's Spanish wording; templates live in the `filing` slice's infrastructure, not inline in use cases.

## 5) Catalogs

- Supplier master and departments come from CSV exports (`TAC_SUPPLIERS_CSV`, `TAC_DEPARTMENTS_CSV`), read through `CsvSupplierCatalog` / `CsvDepartmentCatalog`. Reload is an audited action.
- NITs are normalized (digits only, verification digit validated) before comparison.

## 6) Optional Claude classifier

- Off by default: `TAC_LLM_ENABLED=false`. When off, the adapter is not constructed.
- Called only when the rules classifier margin is below `TAC_MIN_CLASSIFICATION_MARGIN`.
- Personal data is masked before sending (names, ID numbers, bank accounts, e-mails, phones).
- Output is parsed into the same domain types and passes through the same rules; it never triggers actions directly.
- Model id from `TAC_LLM_MODEL`; check current model names and prices with the `claude-api` skill, not from memory.
- Tests use a fake; no network calls in the test suite.

## 7) Checklist

| # | Check |
|---|---|
| 1 | Config read only via `Settings`; new vars in `.env.example`? |
| 2 | Adapter behind a port and wired in `container.py`? |
| 3 | OCR local; confidence reported; low confidence -> review? |
| 4 | No real e-mail sending; outbox only? |
| 5 | LLM off by default, masked input, output re-validated, faked in tests? |
| 6 | No secrets in code or logs? |
