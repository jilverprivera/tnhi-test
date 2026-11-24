---
name: infrastructure-services
description: Rules for Docket's external integrations as hexagonal adapters — settings via TAC_ env vars, .eml reading, PDF text and local Tesseract OCR, simulated outbox stored as DB rows (no real e-mail sending), CSV catalogs, and the optional Claude classifier (off by default, masked data). Use when adding or changing any adapter, environment variable or external dependency in api/.
---

# Skill — Infrastructure services (adapters)

## Goal

Every external capability is an adapter behind a port, configured from one place, replaceable in tests by a fake.

## 1) Configuration — single source of truth (HARD RULE)

- All configuration comes from `app/shared/config.py` (`Settings`, pydantic-settings, `env_prefix="TAC_"`).
- Never read `os.environ` / `os.getenv` anywhere else. Adapters receive values from `container.py`. Single existing exception: `app/mcp/server.py` reads `TAC_MCP_HOST` for the HTTP transport (binds to `127.0.0.1` unless it is set; port 8001) because the MCP server has no auth of its own.
- New variable: add a typed field with a safe default to `Settings` and document it in `.env.example`.
- Secrets (`TAC_ANTHROPIC_API_KEY`, `TAC_DATABASE_URL` with credentials) only from the environment; never commit them.

## 2) E-mail input (`ingestion`)

- `.eml` parsing with stdlib `email` + `policy.default` in `ingestion/infrastructure/eml_reader.py`.
- Splitting lives in `ingestion/application/split_documents.py` (`SplitDocuments`). Each useful attachment is a document; the body is a document (name `EMAIL_BODY`) when no useful attachment exists. The original attachment bytes (or the raw `.eml` for body documents) are stored in `DocumentRow.source_file` as evidence.
- Dates normalized to `America/Bogota` (-05:00).
- Real mailbox integration (Microsoft Graph / Gmail API) is future work; it would be another adapter for the same port.

## 3) Text extraction and OCR

- Adapters in `ingestion/infrastructure/text_extractors.py`. Native PDF: `pdfplumber`. Scanned PDF/image: render with `pypdfium2`, OCR with `pytesseract` (`TesseractOcr`, `lang="spa"`), returning text **and** a confidence score.
- OCR is local; no document leaves the server. There is no Dockerfile in the repo: the host must have `tesseract` (with the `spa` language) on `PATH`; if it is missing, OCR returns method `OCR_UNAVAILABLE`.
- Each document records an `extraction_method`: `PDF_TEXT`, `OCR`, `OCR_UNAVAILABLE`, `EXTRACTION_FAILED` (extractor raised), `DOCX`, `XLSX`, `HTML`, `PLAIN_TEXT`, `EMAIL_BODY`, `UNSUPPORTED` (no extractor matched).
- Unreadable methods (`OCR_UNAVAILABLE`, `UNSUPPORTED`, `EXTRACTION_FAILED`, see `UNREADABLE_METHODS` in `filing/domain/rules.py`) or empty text yield the blocking reason `DOCUMENT_UNREADABLE`. Low OCR confidence (< `TAC_MIN_OCR_CONFIDENCE`) yields the blocking reason `LOW_OCR_CONFIDENCE`.
- Extractors implement one `TextExtractor` port (`supports(mime_type, filename)` + `extract(content)`) and are tried in order (`default_extractors()`); the first that supports the MIME type or extension wins.

## 4) Outbox (simulated sending)

- Docket **never sends e-mail**. On approval, messages are composed and stored as rows in the `outbox_messages` table (`OutboxRow`: `kind`, `document_id`, `to_address`, `subject`, `body`), listed at `GET /api/outbox`. No `.eml` files are generated.
- Kinds (`OutboxKind`): `FORWARD_TO_DEPARTMENT`, `RETURN_TO_SENDER`, `REPLY_EXISTING_NUMBER`, `FRAUD_ALERT`.
- Messages are composed in the pure domain function `compose()` in `filing/domain/outbox_composer.py`, with the client's Spanish wording; not inline in use cases.

## 5) Catalogs

- Supplier master and departments come from CSV exports (`TAC_SUPPLIERS_CSV`, `TAC_DEPARTMENTS_CSV`), read through one adapter, `CsvCatalogs` (`catalogs/infrastructure/csv_catalogs.py`) behind the `CatalogSource` port. Replacing the supplier master (`PUT /api/catalogs/suppliers`) is audited (`SUPPLIER_MASTER_REPLACED` / `SUPPLIER_MASTER_REJECTED`).
- NITs are normalized with `normalize_nit` (`shared/domain/identifiers.py`) before comparison; an invalid verification digit yields the reason `NIT_CHECK_DIGIT_INVALID`.

## 6) Optional Claude classifier

- Off by default: `TAC_LLM_ENABLED=false`. Unless it is on **and** `TAC_ANTHROPIC_API_KEY` is set, `container.py` wires `DisabledClassifier` and `ClaudeClassifier` is not constructed.
- Called only when the rules classifier margin is below `TAC_MIN_CLASSIFICATION_MARGIN`.
- Personal data is masked before sending by `mask_personal_data` (`app/shared/domain/privacy.py`, shared with the audit): e-mail addresses, ID/NIT-like dotted numbers and long digit sequences (accounts, phones). Names are **not** masked (known gap).
- Output is parsed into the same domain types and passes through the same rules; it never triggers actions directly.
- Model id from `TAC_LLM_MODEL`; check current model names and prices with the `claude-api` skill, not from memory.
- Tests use a fake client (`FakeMessages` in `api/tests/features/classification/test_assisted_classifier.py`); no network calls in the test suite.

## 6b) Import queue and observability

- Import queue: `JobQueue` port (`ingestion/application/ports.py`), `SqlJobQueue` adapter (tables `import_jobs` / `import_job_files`, compare-and-set claim, `requeue_interrupted()` in `Container.bootstrap()`), `ImportWorker` daemon thread started in the app lifespan when `TAC_WORKER_ENABLED` (default true), polling every `TAC_WORKER_POLL_SECONDS` (0.5). Tests that do not need it set `worker_enabled=False`.
- Observability (`app/shared/infrastructure/observability.py`): JSON logs on the `docket` logger with `request_id` (`X-Request-ID` in/out), one Prometheus registry per app (`GET /metrics`), business counters from `MeteredAuditLog` (never from domain code), `GET /api/ready` (database, ledger_template, ocr `DEGRADED` without Tesseract, import_worker). Metric labels are codes only, never personal data.
- Shared Excel sync: `PeriodicTask` (`app/shared/infrastructure/scheduler.py`) runs `SyncLedger` every `TAC_LEDGER_SYNC_SECONDS` (unset or `0` disables; the template sets 30; approvals always sync). The file is the client's shared book: treat it as concurrently edited by people.

## 7) Checklist

| # | Check |
|---|---|
| 1 | Config read only via `Settings`; new vars in `.env.example`? |
| 2 | Adapter behind a port and wired in `container.py`? |
| 3 | OCR local; confidence reported; low confidence -> review? |
| 4 | No real e-mail sending; outbox rows only? |
| 5 | LLM off by default, masked input, output re-validated, faked in tests? |
| 6 | No secrets in code or logs? |
