# 02 — Features by role

What each person can do and how it is checked. Every acceptance criterion points to the automated test that verifies it. Per-feature technical details in [../features/](../README.md).

Test paths: backend in `api/tests/`, frontend in `web/src/**/__tests__/`, E2E in `web/e2e/`.

## Martha Rojas — filing clerk (`CLERK`)

### F1. Read the mailbox
"Leer buzón" button or `.eml` upload. From the screen both go through the import queue (`POST /api/ingestion/jobs/mailbox` / `POST /api/ingestion/jobs/upload` → `202 IMPORT_QUEUED`); the background `ImportWorker` turns the e-mails into proposals and the screen follows the job (`GET /api/ingestion/jobs/{id}`) with a loading toast, so a month-end peak does not block the request. The synchronous endpoints (`POST /api/ingestion/mailbox`, `POST /api/ingestion/upload`) remain for the CLI and scripts. See [ingestion](../features/ingestion.md).

| Acceptance criterion | Test |
|---|---|
| Each attachment is a document; two invoices in one e-mail are two documents | `api/tests/features/ingestion/test_split_documents.py::test_every_attachment_is_its_own_document` |
| Without attachments, the e-mail body is the document | `test_split_documents.py::test_body_is_the_document_when_there_are_no_attachments` |
| Small signature images are ignored | `test_split_documents.py::test_small_signature_images_are_ignored` |
| An unsupported format or corrupt attachment is flagged, not lost, and does not break the import | `test_split_documents.py::test_unsupported_format_is_flagged_not_dropped`, `::test_corrupt_attachment_is_flagged_not_crashing` |
| The sample mailbox yields 17 documents | `test_split_documents.py::test_real_mailbox_yields_17_documents` |
| The scanned PDF goes through local OCR | `test_split_documents.py::test_scanned_pdf_goes_through_ocr` |
| Dates are in Bogotá time | `test_split_documents.py::test_dates_are_in_bogota_time` |
| Importing twice does not duplicate | `api/tests/features/filing/test_approve_and_correct.py::test_import_is_idempotent` |
| A queued mailbox job runs in the background and records its result; upload jobs run in order and stay idempotent | `api/tests/features/ingestion/test_import_queue.py::test_mailbox_job_runs_and_records_the_result`, `::test_upload_jobs_run_in_order_and_are_idempotent` |
| A failing job is recorded as `FAILED` (`IMPORT_FAILED`) and the queue goes on; a job interrupted by a crash goes back to the queue | `test_import_queue.py::test_a_failing_job_is_recorded_and_the_queue_goes_on`, `::test_jobs_interrupted_by_a_crash_go_back_to_the_queue` |
| Over HTTP: `202 IMPORT_QUEUED`, the worker finishes it with 17 documents and `GET /api/ingestion/jobs` counts it | `api/tests/api/test_observability.py::test_queued_import_is_processed_by_the_worker` |

### F2. See the inbox with proposal, reasons and evidence
`/inbox` screen (pending / review filters, 50 documents per page with "Anterior" / "Siguiente" in the URL, counters from `GET /api/inbox/summary`) and `/documents/[id]` ("Por qué" — why). See [inbox](../features/inbox.md).

| Acceptance criterion | Test |
|---|---|
| What needs review comes first; blocking reasons are shown in Spanish | `web/src/features/inbox/__tests__/mappers.test.ts` |
| In the detail, blocking reasons come first and the mismatching account field is highlighted | `web/src/features/document-review/__tests__/mappers.test.ts` |
| A held invoice is shown as "possible fraud", not just "review" | `web/src/shared/ui/__tests__/StatusBadge.test.tsx` |
| Real flow: the suspicious invoice appears held with the reason visible | `web/e2e/filing-flow.spec.ts` (step "the suspicious invoice is held") |
| The inbox is paginated in SQL (`{items, total, limit, offset}`), filters by several statuses at once, and `limit` is clamped to 200 | `api/tests/api/test_api.py::test_inbox_and_ledger_are_paginated` |

### F3. Filing rules applied automatically
Invoices (master, PO, duplicates, fraud), travel requests, petitions, oversight notices, complaints, quotations and advertising. Sentence → rule → test traceability in [03-solucion](03-solucion.md).

| Acceptance criterion | Test |
|---|---|
| 25 business rules | `api/tests/features/filing/test_rules.py` |
| Colombian business-day terms with holidays | `api/tests/shared/test_business_calendar.py` |
| Same result as the client expects (8/8) and as the full table (17/17) | `api/tests/golden/test_golden.py` |

### F4. Correct a proposal
`POST /api/inbox/{id}/correct` ("Corregir" sheet: what it is, goes to, action, due date, urgent, notes).

| Acceptance criterion | Test |
|---|---|
| The correction keeps the original proposal and is audited with the changed fields | `test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited` |
| An approved document cannot be corrected | `test_approve_and_correct.py::test_approved_documents_cannot_be_corrected` |
| The form rejects filing without a department and malformed dates | `web/src/features/document-review/__tests__/mappers.test.ts` ("correction schema") |

### F5. Approve and file (one or in batch)
`POST /api/inbox/approve`, `POST /api/inbox/approve-ready`.

| Acceptance criterion | Test |
|---|---|
| The filing number is assigned on approval, in reception order (04818…04831) | `test_approve_and_correct.py::test_filing_numbers_are_assigned_on_approval_in_reception_order`, `test_golden.py::test_filing_numbers_continue_the_ledger` |
| "Aprobar listos" (approve ready) only takes READY documents | `test_approve_and_correct.py::test_batch_approval_only_takes_ready_documents`, `::test_ready_only_approval_rejects_documents_that_need_review` |
| An unreadable document cannot be filed without a department | `test_approve_and_correct.py::test_unreadable_document_cannot_be_filed_without_a_department` |
| A suspected fraud is never approved, only escalated to the coordinator (`HOLD_REQUIRES_ESCALATION`, `HOLD_ESCALATED`); "Aprobar listos" skips holds even when corrected to READY | `test_approve_and_correct.py::test_a_suspected_fraud_is_never_approved_only_escalated`, `::test_batch_approval_skips_holds_even_when_corrected_to_ready`, `api/tests/api/test_api.py::test_approve_rejects_holds_and_escalate_alerts_the_coordinator` |
| Two copies of the same invoice in a batch: the second goes to review | `test_approve_and_correct.py::test_duplicate_inside_the_same_batch_needs_review` |
| Approval writes the outbox message (simulated) | `test_approve_and_correct.py::test_approval_writes_simulated_outbox_messages` |
| Real end-to-end flow over HTTP | `api/tests/api/test_api.py::test_full_flow_over_http`, `web/e2e/filing-flow.spec.ts` |

### F6. Discard
`POST /api/inbox/{id}/discard`, with a reason.

| Acceptance criterion | Test |
|---|---|
| A discarded document cannot be discarded again | `test_approve_and_correct.py::test_discarded_documents_cannot_be_discarded_again` |

### F7. Filing ledger and Excel
`/ledger`, `GET /api/ledger` (paginated: `limit`, `offset` → `{items, total, limit, offset}`), `GET /api/ledger/export`, `GET /api/ledger/duplicates`. See [ledger](../features/ledger.md).

| Acceptance criterion | Test |
|---|---|
| The history is loaded from the client's Excel (last 04817) | `api/tests/features/ledger/test_excel_ledger.py::test_ledger_is_seeded_from_the_client_excel` |
| The export keeps original rows and columns | `test_excel_ledger.py::test_export_keeps_original_rows_and_columns` |
| The original in `material/` is never modified | `test_excel_ledger.py::test_original_material_is_never_modified` |
| Duplicates by supplier + number; reports the historical duplicates 04809/04813 | `test_excel_ledger.py::test_duplicate_lookup_is_by_supplier_and_number`, `::test_historical_duplicates_are_reported` |
| Rows Docket wrote are kept in sync in the Excel (a rejected invoice reads "Rechazada - fraude confirmado"); the first sync of the client's book changes nothing | `api/tests/features/filing/test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated`, `api/tests/features/ledger/test_excel_sync.py::test_first_sync_changes_nothing` |
| The shared Excel is synced both ways: rows typed by hand are imported and numbering continues after them; a petition closed in Excel ("Respondido") leaves the deadlines; people's and Docket's edits to the same row are both kept; same cell on both sides → people win and a conflict is recorded; a deleted row is restored; an open Excel is never overwritten; a save during the merge is merged again | `api/tests/features/ledger/test_excel_sync.py` (8 scenarios) |
| Filters use the design-system select; "ALL" means no filter | `web/src/shared/ui/__tests__/FilterSelect.test.tsx`, `web/src/features/ledger/__tests__/mappers.test.ts`, `web/e2e/coordinator.spec.ts` (last step) |
| The ledger is paginated (28 historical rows: page `offset=20, limit=10` returns 8) and page links keep the search | `test_api.py::test_inbox_and_ledger_are_paginated`, `web/src/features/ledger/__tests__/mappers.test.ts` ("keep the search and move the offset") |

### F8. Settings: supplier master and departments
`/settings`, `PUT /api/catalogs/suppliers`.

| Acceptance criterion | Test |
|---|---|
| Lookup by NIT and by domain | `api/tests/features/catalogs/test_catalogs.py::test_master_lookup_by_nit_and_domain` |
| An invalid master is rejected and the previous one kept | `test_catalogs.py::test_invalid_master_upload_is_rejected_and_keeps_the_old_one` |
| Replacing the master is audited | `test_api.py::test_audit_endpoint_and_master_reload_are_audited` |

## Dra. Claudia Herrera — coordinator (`COORDINATOR`)

### F9. This week's deadlines and weekly report
`/deadlines` (the coordinator's home screen), `GET /api/deadlines`, `GET /api/deadlines/weekly-report`.

| Acceptance criterion | Test |
|---|---|
| States: overdue, today, this week, next week, later | `api/tests/features/deadlines/test_deadlines.py::test_week_bounds_and_states` |
| The report includes documents not filed yet (without waiting for Martha) | `test_deadlines.py::test_weekly_report_includes_documents_not_filed_yet` |
| Filed items keep their urgency | `test_deadlines.py::test_filed_deadlines_keep_their_urgency` |
| Business days left in Spanish; "not filed yet" marked | `web/src/features/deadlines/__tests__/mappers.test.ts` |
| Real flow: the coordinator sees deadlines and cannot approve | `web/e2e/filing-flow.spec.ts` (last step) |

### F10. Read everything; filing stays with Martha

| Acceptance criterion | Test |
|---|---|
| No token, no access | `test_api.py::test_requires_a_token` |
| The coordinator cannot approve (`FORBIDDEN`) | `test_api.py::test_coordinator_cannot_approve` |
| She can read the audit trail | `test_api.py::test_audit_endpoint_and_master_reload_are_audited` |

### F11. Phone use and installation (PWA)

| Acceptance criterion | Test |
|---|---|
| Bottom tab bar, no horizontal scroll, installable manifest (`standalone`) | `web/e2e/mobile.spec.ts` |

### F12. Verify invoices held for possible fraud
`/verifications` ("Por verificar"), `GET /api/verifications`, `POST /api/verifications/{id}/release`, `POST /api/verifications/{id}/reject` (body `{"note"}`). Interview: Martha "se la paso a la doctora Claudia para que verifiquen por teléfono con el proveedor". Each card puts what arrived next to the supplier master (bank account, sender e-mail) with the mismatch marked; after the call she releases the invoice or confirms the fraud, with a required note.

| Acceptance criterion | Test |
|---|---|
| A held invoice waits for the coordinator once Martha escalates it ("Alertar a la Dra. Herrera"); before that it is still with the clerk and cannot be resolved | `api/tests/features/filing/test_verify_hold.py::test_held_invoice_waits_for_the_coordinator`, `::test_before_martha_approves_it_is_still_with_the_clerk` |
| Releasing sends it where Martha's purchase-order rule would have (ledger `DELIVERED`, flag `VERIFIED_BY_PHONE`, `FORWARD_TO_DEPARTMENT` in the outbox) | `test_verify_hold.py::test_release_sends_it_where_the_rules_would_have` |
| Rejecting marks the ledger `REJECTED` (`FRAUD_CONFIRMED`) and warns Accounts payable and Procurement | `test_verify_hold.py::test_reject_marks_fraud_and_warns_payables_and_procurement` |
| A note is required and a hold cannot be resolved twice | `test_verify_hold.py::test_cannot_resolve_twice_or_without_a_note` |
| The resolution is audited and the Excel row is updated | `test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` |
| Only the coordinator resolves (`FORBIDDEN` for the clerk; `VERIFICATION_NOTE_REQUIRED`, `HOLD_NOT_PENDING`) | `api/tests/api/test_api.py::test_only_the_coordinator_resolves_held_invoices` |
| The card compares arrived vs master, flags both mismatches, tells unregistered suppliers apart and groups by who has to act | `web/src/features/verifications/__tests__/mappers.test.ts` |
| Real flow: Martha alerts Dra. Herrera about the suspicious invoice ("Enviar alerta"), Dra. Herrera compares, releases it to Accounts payable and the ledger shows it delivered | `web/e2e/coordinator.spec.ts` |

### F13. Her own workspace
Role-based menu (Vencimientos, Por verificar, Libro, Bandeja, Cumplimiento) and home (`/deadlines`, where a summary shows invoices to verify and the clerk's backlog); the inbox opens in read-only supervision mode.

| Acceptance criterion | Test |
|---|---|
| After login she lands on her home with her own menu; the clerk's menu has no "Por verificar" | `web/e2e/coordinator.spec.ts` (steps 1–2) |
| The deadlines screen shows her "1 factura por verificar" card linking to `/verifications` | `web/e2e/coordinator.spec.ts` (step 2) |

### F14. Document retention (Ley 594 de 2000)
`/compliance` ("Cumplimiento"), `GET /api/retention/schedule`, `GET /api/retention?status=&on=&limit=&offset=`, `POST /api/retention/{filing_number}/dispose` (body `{"record_reference"}`, COORDINATOR only). The retention schedule (TRD) per document type is a starting proposal that TAC's Comité Interno de Archivo must approve; terms count from the end of the year the document was received. Disposal deletes the original file and the extracted text but keeps the ledger row as the index (flag `DISPOSED`, Excel note "Eliminado según la Tabla de Retención Documental"). See [records](../features/records.md) and [compliance](../features/compliance.md).

| Acceptance criterion | Test |
|---|---|
| Accounting support (invoices) is kept 10 years from year-end (04818 → 2036-12-31) | `api/tests/features/records/test_retention.py::test_accounting_support_is_kept_ten_years_from_year_end` |
| Nothing is due on the case date; historical rows are covered too (28 + 3 filed) | `test_retention.py::test_nothing_is_due_today`, `::test_historical_rows_are_covered_too` |
| Disposal removes the content, keeps the index and the decision, writes the Excel note and the `RECORD_DISPOSED` event | `test_retention.py::test_dispose_removes_content_and_keeps_the_index` |
| Never before the term (`RETENTION_NOT_EXPIRED`) and never what must be conserved (`DISPOSITION_NOT_ALLOWED`) | `test_retention.py::test_never_before_the_term_and_never_what_must_be_conserved` |
| The preview date only accepts ISO dates; every disposition has a Spanish label | `web/src/features/compliance/__tests__/labels.test.ts` |
| Real flow: the coordinator opens "Cumplimiento" and sees the TRD and that nothing is due | `web/e2e/coordinator.spec.ts` ("compliance: retention schedule and a data subject request") |

### F15. Data subject requests (habeas data, Ley 1581 de 2012)
`/compliance`, `GET /api/privacy/inventory` (personal-data inventory and safeguards), `POST /api/privacy/subject-requests` (body `{"identifier", "kind"}`, COORDINATOR only). Given a national ID or an e-mail, it lists where that person's data is (ledger and inbox) and the legal deadline to answer: inquiry (`INQUIRY`, art. 14) 10 business days, claim (`CLAIM`, art. 15) 15 business days. See [privacy](../features/privacy.md).

| Acceptance criterion | Test |
|---|---|
| Finds an employee by national ID in the inbox and the ledger; an inquiry is due in 10 business days | `api/tests/features/privacy/test_subject_requests.py::test_finds_an_employee_by_national_id` |
| Finds a citizen by e-mail; a claim is due in 15 business days (8-Dec holiday skipped) | `test_subject_requests.py::test_finds_a_citizen_by_email_and_claims_have_15_days` |
| The audit (`PRIVACY_SUBJECT_LOOKUP`) never stores the identifier, only a masked one | `test_subject_requests.py::test_the_audit_never_stores_the_identifier` |
| Too-short identifiers are rejected (`IDENTIFIER_TOO_SHORT`) | `test_subject_requests.py::test_too_short_identifiers_are_rejected` |
| Only the coordinator runs a request and the identifier travels in the body, never in the URL | `test_subject_requests.py::test_only_the_coordinator_runs_subject_requests_and_ids_travel_in_the_body` |
| Real flow: she searches "80.123.456" and sees "Titular ***.456" and the answer deadline | `web/e2e/coordinator.spec.ts` ("compliance: retention schedule and a data subject request") |

## AI assistant over MCP (on behalf of Dra. Herrera)

Tools: `deadlines_this_week`, `weekly_report`, `list_deadlines`, `search_ledger`, `pending_review`, `held_invoices`, `inbox_summary`. See [mcp](../features/mcp.md).

| Acceptance criterion | Test |
|---|---|
| Answers "what is due this week?" | `api/tests/mcp/test_mcp_server.py::test_what_is_due_this_week` |
| A date range includes documents not filed yet | `test_mcp_server.py::test_deadlines_in_a_range_include_unfiled_documents` |
| Searches the ledger and lists what is pending review | `test_mcp_server.py::test_search_ledger_and_pending_review` |
| Lists held invoices with their verification state and fraud reasons | `test_mcp_server.py::test_held_invoices_tool` |
| No tool modifies state | `test_mcp_server.py::test_tools_are_read_only` |

## Cross-cutting

| Acceptance criterion | Test |
|---|---|
| Every mutating action leaves an audit event; the audit is append-only | `api/tests/features/audit/test_audit.py` |
| AI is off by default, only asked when rules are unsure, gets masked data and its refusals fall back to rules | `api/tests/features/classification/test_assisted_classifier.py` |
| Free-text discard reasons are masked before they reach the audit | `api/tests/features/privacy/test_subject_requests.py::test_discard_reasons_are_masked_in_the_audit` |
| Monitoring: `GET /metrics` exposes business counts (proposals, reasons, approvals, import duration) without personal data; `X-Request-ID` is echoed; `GET /api/ready` answers `READY` with database and worker checks. See [observability](../features/observability.md) | `api/tests/api/test_observability.py::test_metrics_expose_business_counts_without_personal_data`, `::test_request_id_and_readiness` |
| On documents written by someone who never saw the code, the result does not fall below the blind baseline (≥ 45/65 correct, ≤ 6 wrong) and no fraud hold or duplicate is silently missed. See [evaluation](../features/evaluation.md) | `api/tests/blind/test_blind_baseline.py` |
| Responses and errors use `UPPER_SNAKE_CASE` codes | `test_api.py::test_responses_use_the_upper_snake_case_envelope`, `::test_validation_errors_are_upper_snake_case`, `::test_unknown_document_returns_a_code` |
