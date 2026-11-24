# Docket — assisted document filing for Terminales Andinas de Carga (TAC)

Loaded at session start. Hard rules live here; details live in `.claude/skills/`.

## 1. Project

Docket does the document-filing ("radicación") work of TAC's clerk (Martha) over a mailbox:

- Reads `.eml` e-mails and attachments: native PDFs, scanned PDFs (local Tesseract OCR), e-mail bodies.
- Classifies each document: `INVOICE`, `TRAVEL_EXPENSE_REQUEST`, `PETITION`, `OVERSIGHT_NOTICE`, `COMPLAINT`, `QUOTATION`, `ADVERTISING`, `OTHER`.
- Extracts fields and applies the clerk's rules: supplier master checks, duplicate invoices, bank-account-change fraud, petition deadlines in Colombian business days.
- Proposes department / action / due date; what it is not sure about goes to human review with reason codes.
- Continues the client's Excel ledger with consecutive filing numbers `TAC-2026-ER-#####` (assigned on approval).
- Exposes the ledger through a **read-only** MCP server ("what is due this week?").
- AI (Claude API) is optional and **OFF by default** (`TAC_LLM_ENABLED=false`): client IT has not approved AI. The core is deterministic rules; LLM output always passes through the same rules.

Case date ("today"): **2026-11-18**. Client material in `material/` (interview, inbox, supplier master, departments, ledger, expected results `material/4-para-medirte/esperado-parcial.csv`).

## 2. Languages and frameworks

- **Backend** (`api/`): Python 3.12+, FastAPI, uv, pytest, ruff, pydantic-settings (env prefix `TAC_`), SQLAlchemy 2 (SQLite on-prem, Postgres on Render), openpyxl, pdfplumber + Tesseract OCR (pytesseract, `spa`), `holidays` (CO), MCP Python SDK, Anthropic SDK (optional adapter).
- **Frontend** (`web/`): TypeScript, Next.js App Router, Tailwind CSS v4 + shadcn/ui, Serwist (PWA), react-hook-form + zod, Jest + React Testing Library, Playwright, pnpm.
- **Deployment**: `docker compose` on-prem; demo backend Docker on Render, frontend on Vercel (fictitious data only).

## 3. Architecture

### Backend: vertical slices + hexagonal inside each slice

```
api/app/
  main.py                # composition root (FastAPI app, routers)
  container.py           # dependency wiring (adapters -> use cases)
  shared/
    config.py            # pydantic-settings, env prefix TAC_
    domain/              # models.py (enums + Decision, Reason, Evidence, Document, Proposal,
                         #   LedgerEntry), business_calendar.py, identifiers.py, pagination.py (Page, PageRequest),
                         #   privacy.py (mask_personal_data, mask_identifier)
    infrastructure/      # db.py (*Row models), http.py (envelope, roles), client_vocabulary.py (English codes <-> client Spanish values),
                         #   observability.py (Prometheus metrics, JSON logs, MeteredAuditLog)
  features/
    catalogs/ ingestion/ classification/ filing/ ledger/ deadlines/ audit/ records/ privacy/
      domain/            # pure business logic, no framework/IO imports
      application/       # ports.py (typing.Protocol) + use cases (one class per use case, __call__)
      infrastructure/    # adapters implementing ports (eml, pdf/ocr, csv, SQLAlchemy, openpyxl, Claude)
      api/               # FastAPI router = driving adapter
  mcp/server.py          # read-only MCP server reusing ledger/deadlines/inbox use cases
api/tests/           # unit tests per slice + golden tests vs esperado-parcial.csv + blind baseline (tests/blind/)
```

**Dependency rule:** `domain <- application <- infrastructure / api`. Domain imports nothing from FastAPI, SQLAlchemy, openpyxl, pdfplumber or the Anthropic SDK. Slices talk to each other only through another slice's application use cases/ports, never through its infrastructure. Wiring happens only in `container.py`.

### Frontend: screaming architecture (features first) + atomic design

```
web/src/
  app/                   # Next routes only; page.tsx composes a feature template
  features/
    inbox/ document-review/ verifications/ ledger/ deadlines/ settings/ compliance/ session/
      components/        # molecules/ organisms/ templates/ specific to the feature
      hooks/  api/  model/ (types + mappers from API codes)  __tests__/
  shared/
    ui/ primitives/ (shadcn generated)  atoms/  molecules/  organisms/  templates/
    lib/ (api client, cn)   i18n/ (es labels for UPPER_SNAKE codes)   theme/ (tokens.css)
web/e2e/            # Playwright
```

No feature imports another feature; shared pieces move to `shared/`. Layer order `primitives -> atoms -> molecules -> organisms -> templates`, never upward. One component per file.

## 4. Conventions

- **All code in English**: modules, functions, variables, comments, test names.
- **Spanish only at user-facing edges**: frontend i18n labels and the client's Excel ledger values (via `client_vocabulary.py`).
- **API values**: every enumerated value, status, reason code and error code is `UPPER_SNAKE_CASE` (`NEEDS_REVIEW`, `EMAIL_ACCOUNT_MISMATCH`, `DOCUMENT_NOT_FOUND`). JSON keys are lowercase `snake_case`. The frontend translates codes to Spanish.
- Python fully type-hinted; TypeScript strict, no `any`.
- Comments only to explain *why*; no decorative section dividers.

## 5. Guardrails (hard rules)

- **`material/` is read-only.** Never write to it; work on copies under `api/data/` or a temp dir.
- **Preserve the client's workbook**: never change the 12 columns or formats; the shared Excel is synced both ways (`SyncLedger`): Docket appends its rows and writes only the cells it changed, people's edits win on conflict, and the file is never written while open (`~$` lock).
- **Nothing irreversible without a human**: documents in review are never forwarded automatically; filing numbers are never reused; a suspected fraud is never approved, only escalated to the coordinator; retention disposal needs the coordinator and the archive committee's record.
- **Every feature ships with bilingual docs**: Markdown in both `docs/en/features/<feature-slug>.md` and `docs/es/features/<feature-slug>.md` (same slug as the api/web feature folder, same structure), listed in `docs/en/README.md` and `docs/es/README.md`. A feature without both docs is not done. Template: `documentation-web` skill.
- **NEVER run a test suite in one go or with unbounded parallelism** — frontend (bare `pnpm test`, `npx jest`, `jest --watch`, high `--maxWorkers`) or backend (bare `uv run pytest` over the whole tree, `pytest -n auto`/xdist, `--looponfail`): it saturates the machine's RAM. Run tests only in chunks through `./scripts/harness-verify.sh` (staged by changed files, a few test files per batch, one batch at a time under a per-runner lock — `pytest` / `jest` / `playwright` — with a RAM guard). The full suite (`--full`) only when the user explicitly asks, and still through the harness.
- **Both stacks ship tests**: every backend use case/domain rule has pytest tests (unit per slice + golden tests vs `material/4-para-medirte/esperado-parcial.csv`); frontend with Jest + RTL; E2E with Playwright (serialized, `--workers=1`).
- Every mutating action leaves an audit event (actor, timestamp `at`, `document_id`, event code, `details`); see `audit-logging` for current events and known gaps.
- **Config is the variable or undefined — never a value in code.** API: only through `app/shared/config.py` (`TAC_*`, every field `X | None = None`); code that needs a setting calls `settings.require("<field>")`, which raises `MissingSettingError`; an unset optional setting means "off". No `?? "…"` / `or "…"` / `${VAR:-…}` fallbacks in code, Dockerfiles or compose. Web: `process.env.DOCKET_*` with no fallback (only `NODE_ENV` is read freely); the case date comes from the API (`shared/lib/case-date.ts`). Tests pass every value explicitly (`make_settings`, `_env_file=None`; Playwright `API_ENV`). No secrets in code; document every var in `api/.env.example` / `web/.env.example`.
- No silent `except`: catch specific exceptions and map them to a domain error code.
- Ask before changing `Dockerfile`, `docker-compose*.yml`, `.env` files or running destructive DB commands.
- Never `git commit`, `git push`, `git stash` or switch branches unless the user asks.

## 6. Verification

```bash
./scripts/harness-verify.sh --backend              # ruff on changed files + pytest batches for changed slices
./scripts/harness-verify.sh --frontend             # pnpm lint + jest batches (--maxWorkers=1)
./scripts/harness-verify.sh --e2e                  # changed Playwright specs, --workers=1
./scripts/harness-verify.sh api/tests/features/ledger/test_x.py   # explicit files
./scripts/harness-verify.sh --all --full           # whole suite, chunked: only when the user asks
cd web && pnpm build                          # frontend build check
```

Defaults: `--changed`, `--batch 3`, `DOCKET_MIN_FREE_MEM_PCT=15`. Report exactly which batches ran. The golden test must stay at 100 %. Checklist before "done": `.claude/CHECKPOINTS.md`.

## 7. Working mode

For multi-step or multi-file work act as the `leader` (`.claude/agents/leader.md`): decompose, delegate to `implementer`, close with a `reviewer` verdict. Notes go to `progress/<topic>/`. Conceptual questions and trivial single-file changes: answer or implement directly. Process: `.claude/skills/harness/SKILL.md`; rules recap: `.claude/RULES.md`.

## 8. Skills index (`.claude/skills/<name>/SKILL.md`)

**Process:** `harness`, `pr-description`

**Backend:** `architecture-api` (slices, hexagonal, use cases, routers) · `nomenclature` (Python naming) · `prisma` (historical name: SQLAlchemy repositories, migrations, Excel ledger adapter) · `audit-logging` · `infrastructure-services` (config, PDF/OCR, e-mail, outbox, optional Claude) · `testing` (pytest, golden tests) · `types` (API contract and codes)

**Frontend (web):** `architecture-web` (before routes/features) · `ui-structure-web` (before components) · `nomenclature-web` · `forms-web` · `theme-web` · `translation-web` · `performance-web` · `testing-web` · `documentation-web` (bilingual feature docs)

**Frontend (mobile/responsive/PWA; folder names are historical, there is no native app):** `architecture-mobile` (mobile-first layouts, PWA shell) · `structure-mobile` (responsive component placement) · `nomenclature-mobile` · `theme-mobile` · `translation-mobile` · `performance-mobile` · `testing-mobile` (Playwright devices, offline) · `documentation-mobile` (PWA/device docs) · `mobile-forms-with-react-hook-form-and-zod-mobile` (touch-friendly forms)

UI/UX design guidance: user-level skills `/apple-design` and `/ui-ux-pro-max`.
