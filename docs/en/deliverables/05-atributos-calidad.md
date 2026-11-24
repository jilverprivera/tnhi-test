# 05 — Quality attributes (ISO/IEC 25010)

Each scenario follows source → stimulus → environment → response → measure, with how it is verified today and what is missing. Figures measured in the API Docker image with the sample mailbox.

## 1. Functional suitability — correctness

| | |
|---|---|
| **Source** | An e-mail in the filing mailbox |
| **Stimulus** | Martha presses "Leer buzón" (read mailbox) |
| **Environment** | Normal operation, master and ledger loaded, OCR available |
| **Response** | Each document gets type, department, action and due date according to the interview rules |
| **Measure** | 8/8 on the client's expected results; 17/17 on the full table; classifier margins ≥ 2; blind set (65 documents never used to tune the rules): 45 correct, 14 routed to a person, 6 wrong, every fraud hold and duplicate caught ([evaluation](../features/evaluation.md)) |
| **Verified today by** | `api/tests/golden/test_golden.py` (must stay at 100 %), `api/tests/features/filing/test_rules.py` (25 rules), `api/tests/shared/test_business_calendar.py`, `api/tests/blind/test_blind_baseline.py` (floor: ≥ 45 correct, ≤ 6 wrong) |
| **Gap** | The blind set is synthetic (written from the interview, not real TAC mail); the 6 blind errors are open; per-type correction rate in production is not measured yet |

## 2. Security — traceability and auditability (accountability, non-repudiation)

| | |
|---|---|
| **Source** | Accounting, Legal or an auditor |
| **Stimulus** | Asks "who filed this, what did the system propose and what did a person change?" |
| **Environment** | Any time after approval |
| **Response** | The audit shows import, proposal, correction (changed fields), approval, discard and the coordinator's resolution of a held invoice (`HOLD_RELEASED` / `HOLD_REJECTED`, with her note in the ledger); the original proposal is kept next to the final decision |
| **Measure** | 100 % of state-changing actions leave an event; 0 endpoints to edit or delete audit |
| **Verified today by** | `api/tests/features/audit/test_audit.py`, `test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited`, `test_api.py::test_audit_endpoint_and_master_reload_are_audited`, `test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` |
| **Gap** | The actor is the role (`CLERK`), not the person (needs SSO); rejected approvals are not audited; audit lives in the same DB (no external sealing) |

## 3. Security — confidentiality and privacy

| | |
|---|---|
| **Source** | TAC IT / an unauthorized user |
| **Stimulus** | "Where do people's, contract and payment data live and who sees them?" / access attempt without a token or with the wrong role |
| **Environment** | On-prem deployment |
| **Response** | Everything stays on TAC's server; local OCR; AI off; free-text discard reasons masked in the audit; data-subject lookups audited with a masked identifier, the identifier sent in the body, never the URL; documents past their retention term disposed of with an approved record (content purged, ledger index kept); metrics carry counts only; no token → 401; the coordinator cannot approve → 403; the clerk cannot resolve a held invoice → 403; token in an httpOnly cookie; read-only MCP bound to localhost |
| **Measure** | 0 bytes of documents leave TAC with the default configuration; 100 % of mutating endpoints require a role: `CLERK`, except resolving held invoices, which requires `COORDINATOR` |
| **Verified today by** | `test_api.py::test_requires_a_token`, `::test_coordinator_cannot_approve`, `::test_only_the_coordinator_resolves_held_invoices`, `test_assisted_classifier.py::test_disabled_by_default`, `::test_personal_data_is_masked_before_leaving_tac`, `test_mcp_server.py::test_tools_are_read_only`, `test_subject_requests.py` (masked identifier, discard reasons masked, coordinator only), `test_retention.py`, `test_observability.py::test_metrics_expose_business_counts_without_personal_data`; see [privacy](../features/privacy.md) and [records](../features/records.md) |
| **Gap** | Demo tokens instead of SSO; no encryption at rest; MCP without authentication; the retention schedule (TRD) values await approval by TAC's Comité Interno de Archivo; AI needs IT approval (DPA, data region) |

## 4. Usability

| | |
|---|---|
| **Source** | Martha (18 years in the role, non-technical) or Dra. Herrera on her phone |
| **Stimulus** | File the backlog since 10-Nov without the developer's help |
| **Environment** | Desktop or phone, in Spanish |
| **Response** | Inbox with what needs review first, "Por qué" (why) with reasons and evidence in Spanish, correction in one sheet, batch "Aprobar listos", downloadable Excel; controls at least 44 px tall on touch; if a view fails to load, a page offers "Reintentar" or "Ingresar de nuevo"; on phone, bottom tab bar and PWA install |
| **Measure** | Complete flow (read, review, correct, approve, export, see deadlines) without leaving the app; 0 horizontal scroll on phone |
| **Verified today by** | `web/e2e/filing-flow.spec.ts`, `web/e2e/mobile.spec.ts`, mapper tests in `web/src/features/*/__tests__/` |
| **Gap** | No timed test with Martha; no formal accessibility audit (WCAG AA) |

### Role-specific views

| | |
|---|---|
| **Source** | Dra. Herrera (coordinator), who supervises and verifies but does not file |
| **Stimulus** | Signs in to see what waits on her and to resolve an invoice held for possible fraud |
| **Environment** | Desktop or phone, in Spanish, after Martha escalated the held invoice ("Alertar a la Dra. Herrera") |
| **Response** | Login takes each role to its own home (`ROLE_HOME`: clerk `/inbox`, coordinator `/deadlines`) with its own menu (`ROLE_NAV`); her deadlines screen opens with "facturas por verificar" and the clerk's backlog; "Por verificar" puts what arrived next to the supplier master (bank account, sender e-mail) with the mismatch marked, and a dialog with a required note to release or confirm fraud; the inbox opens in read-only supervision mode |
| **Measure** | From login to a resolved held invoice in 3 clicks plus the note, without leaving the app; the clerk never sees "Por verificar" and the coordinator never sees filing buttons |
| **Verified today by** | `web/e2e/coordinator.spec.ts`, `web/src/features/verifications/__tests__/mappers.test.ts`, `test_api.py::test_only_the_coordinator_resolves_held_invoices` |
| **Gap** | Not validated with Dra. Herrera herself; no notification (e-mail or push) when a new invoice waits for verification: she sees it when she opens the app or asks the MCP assistant (`held_invoices`) |

## 5. Performance efficiency

| | |
|---|---|
| **Source** | Martha |
| **Stimulus** | Reads one day's mailbox (≈ 40 documents) or a week's backlog |
| **Environment** | On-prem server, single process |
| **Response** | Proposals ready for review |
| **Measure** | Median 20 ms per native PDF or body (max 50 ms); scanned with OCR 1.9 s; 17-document mailbox 2.2 s; approving all 0.2 s. A month-end import is queued (`202 IMPORT_QUEUED`) and returns at once while the background worker processes it; inbox and ledger pages are at most 200 rows (default 50), the inbox paged in SQL |
| **Verified today by** | Manual measurement in the Docker image (`app.cli process` CLI); `test_import_queue.py`, `test_observability.py::test_queued_import_is_processed_by_the_worker`, `test_api.py::test_inbox_and_ledger_are_paginated`; job duration in the `docket_import_job_seconds` metric |
| **Gap** | No automated load test; one worker thread per API process; numbering lock is in-process (not safe across several API processes); the ledger and retention lists are filtered in memory before paging |

## 6. Maintainability — rules as code, slices

| | |
|---|---|
| **Source** | Developer or the lawyer |
| **Stimulus** | Changes a rule (e.g. a term, a holiday, a new department) |
| **Environment** | Development |
| **Response** | The change is made in one place (`filing/domain/rules.py`, `TAC_EXTRA_HOLIDAYS`, master or departments), with its test; the domain does not depend on frameworks |
| **Measure** | A rule change touches 1 domain file + 1 test; the golden table catches regressions |
| **Verified today by** | Per-slice tests in `api/tests/features/`, dependency rule `domain <- application <- infrastructure/api` (see [01-arquitectura](01-arquitectura.md)) |
| **Gap** | Rules live in code, not in a business-editable table; no automated check of the dependency rule (e.g. import-linter) |

## 7. Portability — on-prem or cloud

| | |
|---|---|
| **Source** | TAC IT |
| **Stimulus** | Install on an own server or in the cloud |
| **Environment** | Linux with Docker |
| **Response** | `docker compose up --build` starts web and API with SQLite on a volume; the same image runs on Render with a disk (`render.yaml`) and the web on Vercel |
| **Measure** | 1 command; configuration only through `TAC_*` variables |
| **Verified today by** | Images built and tested locally (OCR verified inside the image) |
| **Gap** | The cloud demo is not deployed yet; Postgres supported but not tested in this delivery |

## 8. Reliability — availability and offline work

| | |
|---|---|
| **Source** | Internet or AI provider outage |
| **Stimulus** | No internet access / the Claude API does not answer or refuses |
| **Environment** | On-prem |
| **Response** | Filing keeps working: it does not depend on the cloud; if AI fails or refuses, rules take over; the PWA shows an offline page and keeps read views cached. Operations can see it: Prometheus metrics at `/metrics`, `/api/ready` (`READY` 200 / `NOT_READY` 503; OCR missing only degrades), JSON logs with `X-Request-ID`; a job interrupted by a crash goes back to the queue on restart |
| **Measure** | 0 external dependencies on the default path |
| **Verified today by** | `test_assisted_classifier.py::test_refusals_fall_back_to_rules`, `::test_disabled_by_default`; PWA `/offline` route; `test_observability.py::test_request_id_and_readiness`, `test_import_queue.py::test_jobs_interrupted_by_a_crash_go_back_to_the_queue`; see [observability](../features/observability.md) |
| **Gap** | Single server, no replica; metrics exist but no alert rules or dashboards are shipped; no automated backups |

### Integrity of the shared Excel

| | |
|---|---|
| **Source** | Accounting, Legal or Martha working on the shared Excel while Docket files |
| **Stimulus** | Someone types a row by hand, writes "Respondido" in a status, adds a note, deletes a row, or has the file open while Docket approves |
| **Environment** | Normal operation; the book in a shared folder |
| **Response** | `SyncLedger` merges both ways cell by cell: hand-typed rows are imported and numbering continues after them; people's edits flow into the ledger (a closed petition leaves the deadlines); same cell changed on both sides → people win and a conflict is shown on `/ledger`; a deleted row is restored; the file is never written while open (`LOCKED`, written later) nor if it changed during the merge (merged again, atomic replace) |
| **Measure** | 0 cells typed by people lost; 0 filing numbers repeated or missing; 0 writes over an open file |
| **Verified today by** | `api/tests/features/ledger/test_excel_sync.py` (8 scenarios); see [ledger](../features/ledger.md#two-way-sync-with-the-shared-excel) |
| **Gap** | The book is a file in a local or mounted folder: a SharePoint / Google Drive adapter is pending; lock detection relies on Excel's `~$` file; the numbering lock and the sync are single-process |

## 9. Cost

| | |
|---|---|
| **Source** | Administrative and financial management |
| **Stimulus** | 200 documents per week (≈ 870/month) |
| **Environment** | On-prem production |
| **Response** | Rules path on own CPU; AI only if enabled and only for ambiguous docs |
| **Measure** | ≈ US$ 0 marginal with rules; ≈ US$ 0.01/month with Haiku 5.5 for the 20 % ambiguous; ≈ US$ 0.91/month with Sonnet 5.5 for everything (prices to verify) |
| **Verified today by** | Calculation with ≈ 500 input + 5 output tokens per call; see [00-resumen-ejecutivo](00-resumen-ejecutivo.md#c-what-it-costs-to-process-a-document) |
| **Gap** | Real token usage is not recorded; cloud demo cost to be confirmed on each provider's pricing page |
