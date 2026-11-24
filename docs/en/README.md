# Docket — documentation (English)

Docket does the document-filing ("radicación") work of Terminales Andinas de Carga (TAC) over the filing mailbox: it reads e-mails and attachments, classifies each document, applies the clerk's rules, proposes department / action / due date, and — only after the clerk approves — continues the client's Excel ledger with consecutive filing numbers `TAC-2026-ER-#####`. A read-only MCP server lets an AI assistant answer "what is due this week?".

Spanish version: [../es/README.md](../es/README.md).

## Deliverables

Interview documents, in `deliverables/`. Start with the executive summary.

| Document | What it answers |
|---|---|
| [00 — Executive summary](deliverables/00-resumen-ejecutivo.md) | Components and where AI is involved, how we know it is right, cost, time saved, technical debt (2–3 pages, one diagram) |
| [01 — Architecture](deliverables/01-arquitectura.md) | C4, slices and the hexagonal rule, frontend, data flow, deployment, where each piece of data lives and who sees it |
| [02 — Features](deliverables/02-features.md) | Features by role with acceptance criteria linked to tests |
| [03 — Solution](deliverables/03-solucion.md) | Traceability Martha's sentence → rule → code → test; mailbox result; judgment calls |
| [04 — Domain model](deliverables/04-modelo-dominio.md) | Entities, enumerations and the document life cycle |
| [05 — Quality attributes](deliverables/05-atributos-calidad.md) | ISO 25010 scenarios with measure, verification and gaps |

## Backend features

| Feature | What it covers |
|---|---|
| [Ingestion](features/ingestion.md) | Importing `.eml` e-mails, splitting them into documents, text extraction and local OCR; persistent import queue with a background worker for month-end peaks |
| [Classification](features/classification.md) | Document type and field extraction; optional AI second opinion (off by default) |
| [Filing](features/filing.md) | Business rules, reason codes, review, correction, approval, filing numbers, outbox, held-invoice verification |
| [Ledger](features/ledger.md) | The client's Excel ledger synced both ways with the shared file, numbering, paginated search, export, duplicates |
| [Deadlines](features/deadlines.md) | Business-day terms, deadline states, the coordinator's weekly report |
| [Catalogs](features/catalogs.md) | Supplier master and departments |
| [Audit](features/audit.md) | Append-only trail of who did what, with personal data masked |
| [Records retention](features/records.md) | Retention schedule (TRD, Ley 594 de 2000), records due for disposition, controlled disposal that keeps the index |
| [Personal data protection](features/privacy.md) | Habeas data (Ley 1581 de 2012): personal data inventory, data subject lookups with legal deadlines, shared masking |
| [Observability](features/observability.md) | Prometheus metrics at `/metrics`, readiness `GET /api/ready`, JSON logs with `X-Request-ID` |
| [Evaluation](features/evaluation.md) | Golden table (8/8, 17/17) and blind set (45/65 correct, 14 to a person, 6 wrong); no-tuning policy |
| [MCP server](features/mcp.md) | Read-only tools for an AI assistant |

## Frontend features

Screens of the web app (`web/`, Next.js). The ledger and deadlines screens are documented in the same doc as their backend slice (shared slug).

| Feature | What it covers |
|---|---|
| [Inbox](features/inbox.md) | The clerk's queue: queued mail import, filters, counters, pagination, batch approval of `READY` documents |
| [Document review](features/document-review.md) | One document: original, proposal, reasons, fields, history; approve, correct, discard; alert the coordinator about a suspected fraud |
| [Verifications](features/verifications.md) | `/verifications`: the coordinator's held invoices, arrived vs supplier master, release or confirm fraud (backend in the filing slice) |
| [Ledger](features/ledger.md#the-screen-ledger) | `/ledger`: search, historical duplicates alert, table/cards, Excel download |
| [Deadlines](features/deadlines.md#the-screen-deadlines) | `/deadlines`: weekly report for the coordinator, print, offline reading |
| [Settings](features/settings.md) | System status (readiness, import queue), AI status, supplier master (and its replacement), departments, simulated outbox |
| [Compliance](features/compliance.md) | `/compliance`: the coordinator's retention schedule, records due for disposal, personal data inventory and data subject requests |
| [Session and app shell](features/session.md) | Login, httpOnly token cookie, route guard, header, sidebar and tab bar, roles in the UI |
| [PWA](features/pwa.md) | Manifest, icons, install, Serwist service worker, what is (and is not) cached offline |

## Roles

| Role | Person | Can |
|---|---|---|
| `CLERK` | Martha Rojas, filing clerk | import, correct, discard, approve, alert the coordinator about a suspected fraud, replace the supplier master, read everything |
| `COORDINATOR` | Dra. Claudia Herrera, administrative and financial coordinator | release or reject held invoices after calling the supplier, dispose of records whose retention ended, run data subject lookups, read everything (inbox, ledger, deadlines, outbox) |
| AI assistant (MCP) | on behalf of either | read-only tools |

API conventions: every response is `{"code": "UPPER_SNAKE", "data": ...}`; errors are `{"code": "...", "detail": {...}}`. Authenticate with `Authorization: Bearer <token>` (`TAC_CLERK_TOKEN`, default `martha-demo`; `TAC_COORDINATOR_TOKEN`, default `herrera-demo`).

## How to run the backend

From the repository root (`material/` is never written; data goes to `api/data/` or the directory you pass):

```bash
cd api
uv sync                                               # install dependencies
uv run uvicorn app.main:app --reload                  # REST API on http://localhost:8000 (docs at /docs)
uv run python -m app.cli process --data-dir /tmp/docket --approve-all   # whole mailbox end to end, prints proposals
uv run python -m app.mcp.server                       # read-only MCP server (stdio); add --http for :8001
```

Tests — never run the whole suite in one go; use the harness from the repository root:

```bash
./scripts/harness-verify.sh --backend                 # ruff + pytest batches for changed slices
./scripts/harness-verify.sh api/tests/golden/test_golden.py   # explicit files
```

Settings (`TAC_*`, see `api/app/shared/config.py` and the annotated `api/.env.example`). **Nothing has a default in code:** each setting is its variable or undefined. Required ones (`TAC_DATA_DIR`, `TAC_DATABASE_URL`, `TAC_INBOX_DIR`, `TAC_SUPPLIERS_CSV`, `TAC_DEPARTMENTS_CSV`, `TAC_LEDGER_XLSX`, `TAC_COMPANY_NIT`, `TAC_FILING_PREFIX`, `TAC_OCR_LANGUAGE`, `TAC_MIN_OCR_CONFIDENCE`, `TAC_MIN_CLASSIFICATION_MARGIN`, plus `TAC_WORKER_POLL_SECONDS` when the worker is on and `TAC_MCP_HOST`/`TAC_MCP_PORT` for MCP over HTTP) fail with `MissingSettingError: TAC_<NAME> is not set`. Optional ones mean "off" when unset: `TAC_TODAY` (real date), `TAC_CLERK_TOKEN`/`TAC_COORDINATOR_TOKEN` (that role cannot sign in), `TAC_CORS_ORIGINS` (no CORS), `TAC_LLM_ENABLED`+`TAC_ANTHROPIC_API_KEY`+`TAC_LLM_MODEL` (AI only with all three), `TAC_WORKER_ENABLED`, `TAC_LEDGER_SYNC_SECONDS` (only on approve/export/demand), `TAC_EXTRA_HOLIDAYS`. The API reads `api/.env` wherever it is started from, and relative paths resolve against `api/`. The web needs only `DOCKET_API_URL`; the case date comes from the API. Scanned PDFs need Tesseract with Spanish data (`tesseract-ocr`, `tesseract-ocr-spa`); without it they go to human review as `DOCUMENT_UNREADABLE`.
