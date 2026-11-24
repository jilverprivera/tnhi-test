---
name: audit-logging
description: Enforces mandatory, immutable audit events in the Docket backend for every mutating or decision action (import, approve, correct, send to review, void, batch approve, catalog reload), including system proposal vs human correction for accuracy metrics. Use when creating or modifying endpoints, use cases or any state-changing flow in backend/.
---

# Skill — Audit events (mandatory)

## Goal

Answer for any document: **who** did **what**, **when**, on **which** resource, and **how the human decision differed from the system proposal**. The audit trail is also the data source for accuracy metrics (correction rate per document type) and for the time-saved measurement.

## Data model

`AuditRow` (SQLAlchemy, table `audit_events`, in `app/shared/infrastructure/db.py`), append-only:

| Field | Notes |
|---|---|
| `id` | UUID |
| `occurred_at` | timezone-aware UTC timestamp |
| `actor` | `CLERK`, `COORDINATOR`, `SYSTEM` (automatic steps) or `CLI` |
| `document_id` | inbox document id (`01.eml__0`) or null for batch-level events |
| `event` | `UPPER_SNAKE_CASE`: `EMAILS_IMPORTED`, `DOCUMENT_PROPOSED`, `DOCUMENT_APPROVED`, `DOCUMENT_CORRECTED`, `DOCUMENT_DISCARDED` (add new codes here when a new mutation appears) |
| `details` | JSON, `snake_case` keys: `filing_number`, `action`, `department`, `corrected`, `changes`, `reasons`, `status` |

Rows are never updated or deleted. No UPDATE/DELETE path exists in the adapter.

## Ownership

Audit lives in its own slice, `app/features/audit/`: `application/ports.py` (`AuditLog` Protocol: `record(actor, event, document_id=None, **details)` and `list(document_id=None)`), `application/list_audit.py` (`ListAudit`), `infrastructure/sql_audit_log.py` (`SqlAuditLog`), `api/router.py` (`GET /api/audit`). Other slices depend on the `AuditLog` port (injected by `app/container.py`), never on the SQLAlchemy adapter.

## When to record (HARD RULE)

| Situation | Record |
|---|---|
| Import of e-mails, proposal creation | Yes (`SYSTEM` actor) |
| Approve, correct, send to review, void, batch approve | Yes |
| Filing number assigned | Yes, in the same transaction as the ledger entry |
| Fraud hold, duplicate detected | Yes |
| Catalog reload | Yes |
| Read-only list/detail, MCP tools | No |
| Rejected attempt on a mutating endpoint (e.g. approving a `NEEDS_REVIEW` doc in a batch) | Yes, with the error code |

## Implementation

- Call `audit.record(...)` from the use case that performs the mutation, after the business step succeeds (or on a business rejection).
- When the write and the audit must be atomic (filing number + ledger entry), share the same session/unit of work.
- If only the audit write fails on a non-critical path, log it with `logging` and do not hide the primary result; never swallow the error silently.
- On correction, always store both the proposal and the human values so accuracy per field can be computed.

## Privacy

- Never store full bank account numbers, ID numbers (cédula) or e-mail bodies in `payload`; mask (`****7890`) or reference by document id.
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
