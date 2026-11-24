---
name: audit-logging
description: Enforces mandatory, immutable audit events in the Docket backend for every mutating or decision action (import, proposal, approve, batch approve, correct, discard, held-invoice verification, supplier master replacement), including system proposal vs human correction for accuracy metrics. Use when creating or modifying endpoints, use cases or any state-changing flow in api/.
---

# Skill — Audit events (mandatory)

## Goal

Answer for any document: **who** did **what**, **when**, on **which** resource, and **how the human decision differed from the system proposal**. The audit trail is also the data source for accuracy metrics (correction rate per document type) and for the time-saved measurement.

## Data model

`AuditRow` (SQLAlchemy, table `audit_events`, in `app/shared/infrastructure/db.py`), append-only:

| Field | Notes |
|---|---|
| `id` | integer, autoincrement (also the list order) |
| `at` | timezone-aware UTC timestamp (`utcnow`), indexed |
| `actor` | role from the bearer token (`CLERK`, `COORDINATOR`), `SYSTEM` (automatic steps) or `CLI` |
| `document_id` | inbox document id (`01.eml__0`) or null for batch-level events |
| `event` | `UPPER_SNAKE_CASE`. Emitted today (`grep -rn '\.record(' api/app`): `EMAILS_IMPORTED`, `DOCUMENT_PROPOSED`, `DOCUMENT_APPROVED`, `DOCUMENT_CORRECTED`, `DOCUMENT_DISCARDED`, `SUPPLIER_MASTER_REPLACED`, `SUPPLIER_MASTER_REJECTED`, `HOLD_ESCALATED`, `HOLD_RELEASED`, `HOLD_REJECTED`, `RECORD_DISPOSED`, `PRIVACY_SUBJECT_LOOKUP`, `LEDGER_MANUAL_ROW_IMPORTED`, `LEDGER_EDIT_MERGED`, `LEDGER_SYNC_CONFLICT`, `LEDGER_ROW_RESTORED` (add new codes here when a new mutation appears) |
| `details` | JSON, `snake_case` keys: `imported`, `skipped`, `status`, `reasons`, `filing_number`, `action`, `department`, `corrected`, `changes`, `reason`, `suppliers`, `missing_columns` |

Rows are never updated or deleted. No UPDATE/DELETE path exists in the adapter.

## Ownership

Audit lives in its own slice, `app/features/audit/`: `application/ports.py` (`AuditLog` Protocol: `record(actor, event, document_id=None, **details)` and `list(document_id=None)`), `application/list_audit.py` (`ListAudit`), `infrastructure/sql_audit_log.py` (`SqlAuditLog`, each `record` commits in its own session), `api/router.py` (`GET /api/audit?document_id=...`, any role, envelope code `AUDIT_LISTED`; items expose `at`, `actor`, `event`, `document_id`, `details`). Other slices depend on the `AuditLog` port (injected by `app/container.py`), never on the SQLAlchemy adapter.

## When to record (HARD RULE)

| Situation | Record |
|---|---|
| Import of e-mails (`EMAILS_IMPORTED`, importing actor) and proposal creation (`DOCUMENT_PROPOSED`, `SYSTEM` actor, with `status` and `reasons`) | Yes |
| Approve / batch approve (`DOCUMENT_APPROVED`, with `filing_number`, `action`, `department`, `corrected`) | Yes |
| Correct (`DOCUMENT_CORRECTED`, with `changes`), discard (`DOCUMENT_DISCARDED`, with `reason`) | Yes |
| Suspected fraud escalated by the clerk (`HOLD_ESCALATED` instead of `DOCUMENT_APPROVED`, same details; `EscalateHold`) | Yes |
| Retention disposal (`RECORD_DISPOSED`, `filing_number`, `record_reference` masked; `DisposeRecord`) and data subject lookup (`PRIVACY_SUBJECT_LOOKUP`, `kind`, `identifier` masked with `mask_identifier`, `matches`; `FindDataSubject`) | Yes |
| Fraud hold, duplicate detected | Recorded as reason codes inside `DOCUMENT_PROPOSED.details.reasons` (no separate event) |
| Held-invoice verification by the coordinator (`HOLD_RELEASED` / `HOLD_REJECTED`, with `filing_number`, `department`; the note is stored in `InboxItem.hold_resolution`) | Yes (recorded by `VerifyHold`) |
| Supplier master upload (`SUPPLIER_MASTER_REPLACED`, or `SUPPLIER_MASTER_REJECTED` with `missing_columns`) | Yes (recorded from `catalogs/api/router.py`) |
| Read-only list/detail, MCP tools | No |
| Rejected attempt on a mutating endpoint (e.g. approving a `NEEDS_REVIEW` doc in a batch) | **Known gap / to do**: not recorded today (`DocumentNotApprovableError` etc. are raised without an audit event). New code should record it with the error code |

There is no void or "send to review" flow in the code today; if one is added, it must record an event.

## Implementation

- Call `audit.record(...)` from the use case that performs the mutation, after the business step succeeds (or on a business rejection).
- Atomicity today: the filing-number assignment is **not** in the same transaction as the audit write. `ApproveDocuments` serializes assignment with an in-process `threading.Lock` (`_SEQUENCE_LOCK`) and relies on the DB unique constraint (`ledger_entries.sequence`, `documents.filing_number`); the ledger append, inbox update, outbox put and `DOCUMENT_APPROVED` audit each commit in their own session. Making them one unit of work is a known gap / to do.
- If only the audit write fails on a non-critical path, log it with `logging` and do not hide the primary result; never swallow the error silently.
- On correction, the audit stores the changed fields (`changes`); the original proposal is kept immutable in `DocumentRow.proposal` next to the current `decision`, so proposal vs human values can be compared per field.

## Privacy

- Never store full bank account numbers, ID numbers (cédula) or e-mail bodies in `details`; mask (`****7890`) or reference by document id.
- Free text a person types goes through `mask_personal_data` (`app/shared/domain/privacy.py`) before `record(...)`: `DOCUMENT_DISCARDED.details.reason`, `RECORD_DISPOSED.details.record_reference`. Identifiers use `mask_identifier` (last 4 characters). Names are not masked (pattern-based).
- The container wraps the adapter in `MeteredAuditLog` (`shared/infrastructure/observability.py`), which also increments Prometheus counters for some events; labels carry codes only, never personal data.
- No API keys or tokens in payloads or logs.

## Testing

- Use-case tests assert the expected `event`, `document_id` and `details` were recorded (through the container's `list_audit`, or a fake `AuditLog` collecting events).
- Adapter test: events persist and there is no update/delete method.

## Checklist

| # | Check |
|---|---|
| 1 | Every mutating use case records an event? |
| 2 | Event code `UPPER_SNAKE_CASE` and in the list above (or added to it)? |
| 3 | Proposal vs correction stored on corrections? |
| 4 | Sensitive data masked? |
| 5 | Tests assert the audit call? |
