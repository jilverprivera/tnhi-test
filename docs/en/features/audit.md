# Audit

## Purpose

An append-only trail of **who did what, when and on which document**, and of how the human decision differed from the system's proposal. It answers Martha's main condition — being able to see what the system did and why — and Dra. Herrera's concern about who touches sensitive data.

## Who uses it

- **Clerk (CLERK, Martha)**: sees the trail of a document in its detail (`GET /api/inbox/{id}` → `audit`).
- **Coordinator (COORDINATOR, Dra. Herrera)**: same; supervises corrections and approvals, and her own releases and rejections of held invoices are audited (`HOLD_RELEASED` / `HOLD_REJECTED`).
- **AI assistant via MCP**: no access; MCP tools are read-only and do not write audit events.
- **Every mutating use case**: writes through the `AuditLog` port.

## How it works

1. Use cases call `audit.record(actor, event, document_id, **details)` after the business step succeeds. The port lives in `api/app/features/audit/application/ports.py`; the adapter `SqlAuditLog` (`audit/infrastructure/sql_audit_log.py`) inserts a row in `audit_events` (`id`, `at` UTC, `actor`, `event`, `document_id`, `details` JSON).
2. The adapter has **no update or delete** method.
3. `ListAudit` returns events in insertion order, optionally filtered by document.
4. The container wraps the adapter in `MeteredAuditLog` (`shared/infrastructure/observability.py`): every event is written exactly as before and some also increment a Prometheus counter (see [observability](observability.md)). Use cases do not know about it.
5. Free text a person types is **masked** before it is stored (`mask_personal_data`, `shared/domain/privacy.py`): e-mails → `[EMAIL]`, IDs/NITs → `[ID]`, long numbers → `[NUMBER]`. A data subject's identifier is reduced to its last 4 characters (`mask_identifier`).

Events written today:

| Event | Written by | Actor | Details |
|---|---|---|---|
| `DOCUMENT_PROPOSED` | `ImportEmails` (per document) | `SYSTEM` | `status`, `reasons` |
| `EMAILS_IMPORTED` | `ImportEmails` (per batch, `document_id` null) | caller role (`CLERK`, `CLI`, `EVALUATION`; for a queued import, the actor stored in the job) | `imported`, `skipped` |
| `DOCUMENT_CORRECTED` | `CorrectDocument` | `CLERK` | `changes` (field → new value) |
| `DOCUMENT_DISCARDED` | `DiscardDocument` | `CLERK` | `reason` (masked) |
| `DOCUMENT_APPROVED` | `ApproveDocuments` | `CLERK` / `CLI` | `filing_number`, `action`, `department`, `corrected` |
| `HOLD_ESCALATED` | `EscalateHold` (suspected fraud: filed `ON_HOLD`, `FRAUD_ALERT` to the coordinator; replaces `DOCUMENT_APPROVED` for holds) | `CLERK` / `CLI` | `filing_number`, `action`, `department`, `corrected` |
| `HOLD_RELEASED` | `VerifyHold` (released after the phone call) | `COORDINATOR` | `filing_number`, `department` |
| `HOLD_REJECTED` | `VerifyHold` (fraud confirmed) | `COORDINATOR` | `filing_number`, `department` |
| `SUPPLIER_MASTER_REPLACED` | `PUT /api/catalogs/suppliers` (`document_id` null) | `CLERK` | `suppliers` (count) |
| `SUPPLIER_MASTER_REJECTED` | `PUT /api/catalogs/suppliers` with missing columns (`document_id` null) | `CLERK` | `missing_columns` |
| `RECORD_DISPOSED` | `DisposeRecord` (retention, see [records](records.md); `document_id` null for historical rows) | `COORDINATOR` | `filing_number`, `record_reference` (masked) |
| `LEDGER_MANUAL_ROW_IMPORTED` / `LEDGER_EDIT_MERGED` / `LEDGER_SYNC_CONFLICT` / `LEDGER_ROW_RESTORED` | `SyncLedger` (shared Excel sync, see [ledger](ledger.md)) | caller role, or `SYSTEM` for approvals and the periodic sync | `filing_number`; `columns` (edit merged) or `column` (conflict) |
| `PRIVACY_SUBJECT_LOOKUP` | `FindDataSubject` (habeas data, see [privacy](privacy.md); `document_id` null) | `COORDINATOR` | `kind`, `identifier` (masked, e.g. `***.456`), `matches` (count) |

The verification note itself is stored in the inbox item's `hold_resolution` and in the ledger flags, not in the event details.
The original proposal is also kept in the inbox item (`proposal` is never mutated; `GET /api/inbox/{id}` returns `proposal_decision` next to `decision` and `was_corrected`), so the proposal-vs-correction comparison is always available.

## Business rules

| Rule | Source | Where in code |
|---|---|---|
| She must be able to see what was done and why | Martha: *"Que yo pueda ver qué hizo y por qué. No quiero que algo mande las cosas solo y yo no me entere: si se equivoca, la que responde soy yo."* | `DOCUMENT_PROPOSED` with reasons; `DOCUMENT_APPROVED` |
| Know who sees and handles the data | Dra. Herrera: *"La gente de sistemas va a querer saber dónde queda todo eso y quién lo ve."* | actor on every event |
| Every mutating action leaves an event; proposal vs correction kept | Project guardrail | `record(...)` calls; `InboxItem.proposal` immutable |
| A suspected fraud leaves a distinct trail: it is escalated, never "approved" | User decision on fraud handling | `EscalateHold` → `HOLD_ESCALATED` |
| The audit itself must not become a copy of personal data | Ley 1581 de 2012; Dra. Herrera: *"les pido cuidado con la información"* | `mask_personal_data` (discard reasons, disposal records), `mask_identifier` (subject lookups) |
| The coordinator's phone verification of a held invoice is traceable | Martha: *"se la paso a la doctora Claudia para que verifiquen por teléfono con el proveedor"* | `VerifyHold` → `HOLD_RELEASED` / `HOLD_REJECTED` |

## API endpoints / screens

| Method | Path | Role | Request | Success `code` |
|---|---|---|---|---|
| GET | `/api/inbox/{id}` | any | — | `DOCUMENT_FOUND`; `data.audit` holds the document's events |
| GET | `/api/audit` | any | optional `document_id` | `AUDIT_LISTED` (all events, or only the document's) |

Event shape: `{"at": "...", "actor": "CLERK", "event": "DOCUMENT_APPROVED", "document_id": "01.eml__0", "details": {...}}`.

## Codes

| Code | Meaning (EN) | Significado (ES) | Blocking? |
|---|---|---|---|
| `DOCUMENT_PROPOSED` | The system proposed a decision for a document | El sistema propuso una decisión para un documento | — |
| `EMAILS_IMPORTED` | A batch of e-mails was imported | Se importó un lote de correos | — |
| `DOCUMENT_CORRECTED` | A person changed the proposal | Una persona cambió la propuesta | — |
| `DOCUMENT_DISCARDED` | A person discarded the document | Una persona descartó el documento | — |
| `DOCUMENT_APPROVED` | A person approved it (filing number, if any, assigned) | Una persona lo aprobó (con radicado, si aplica) | — |
| `HOLD_ESCALATED` | The clerk alerted the coordinator about a suspected fraud (filed on hold) | La auxiliar alertó a la coordinadora de un posible fraude (radicada como retenida) | — |
| `RECORD_DISPOSED` | A record's content was destroyed under the retention schedule; its index remains | Se eliminó el contenido de un registro según la TRD; queda su índice | — |
| `LEDGER_MANUAL_ROW_IMPORTED` / `LEDGER_EDIT_MERGED` / `LEDGER_SYNC_CONFLICT` / `LEDGER_ROW_RESTORED` | Shared Excel sync: hand-typed row imported / people's edit merged / same cell changed on both sides (people win) / deleted row restored | Sincronización del Excel compartido: fila a mano importada / edición traída / misma celda cambiada en ambos lados (gana la persona) / fila borrada restaurada | — |
| `PRIVACY_SUBJECT_LOOKUP` | The coordinator looked up a data subject (identifier masked) | La coordinadora buscó a un titular (identificador enmascarado) | — |
| `HOLD_RELEASED` | The coordinator verified a held invoice by phone and released it | La coordinadora verificó por teléfono una factura retenida y la liberó | — |
| `HOLD_REJECTED` | The coordinator confirmed a held invoice as fraud | La coordinadora confirmó como fraude una factura retenida | — |
| `SUPPLIER_MASTER_REPLACED` | The supplier master was replaced | Se reemplazó el maestro de proveedores | — |
| `SUPPLIER_MASTER_REJECTED` | A supplier master upload was rejected (missing columns) | Se rechazó un maestro de proveedores cargado (faltan columnas) | — |
| `AUDIT_LISTED` | Audit events returned | Eventos de auditoría devueltos | — |
| `SYSTEM`, `CLERK`, `COORDINATOR`, `CLI`, `EVALUATION` | Actor values | Valores de actor | — |

## Limitations

- The actor is a **role**, not a named person (shared demo tokens); real identity needs SSO.
- Not audited yet: rejected attempts (e.g. `DOCUMENT_NEEDS_REVIEW` on batch approval, `FORBIDDEN`, `HOLD_NOT_PENDING`).
- The approval's audit event and the ledger row are written in separate transactions.
- Masking is pattern-based: personal **names** typed in a discard reason are not removed.
- Append-only is enforced by the code (no update/delete path), not by database permissions.

## How it is tested

- `api/tests/features/audit/test_audit.py`: the adapter has no update/delete/remove; import + approval leave 17 `DOCUMENT_PROPOSED`, `EMAILS_IMPORTED` and `DOCUMENT_APPROVED` with actor `CLERK` and `filing_number` `TAC-2026-ER-04818`.
- `api/tests/features/filing/test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited`.
- `api/tests/features/filing/test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` (`HOLD_REJECTED`).
- `api/tests/api/test_api.py::test_audit_endpoint_and_master_reload_are_audited` (`GET /api/audit` → `AUDIT_LISTED` with `SUPPLIER_MASTER_REJECTED`).
- `HOLD_ESCALATED`: `api/tests/features/filing/test_approve_and_correct.py::test_a_suspected_fraud_is_never_approved_only_escalated`, `api/tests/api/test_api.py::test_approve_rejects_holds_and_escalate_alerts_the_coordinator`.
- `RECORD_DISPOSED`: `api/tests/features/records/test_retention.py::test_dispose_removes_content_and_keeps_the_index`.
- `PRIVACY_SUBJECT_LOOKUP` and masked discard reasons: `api/tests/features/privacy/test_subject_requests.py::test_the_audit_never_stores_the_identifier`, `::test_discard_reasons_are_masked_in_the_audit`.

```bash
./scripts/harness-verify.sh api/tests/features/audit/test_audit.py
```

## Changelog

- 2026-11-24: events `HOLD_RELEASED` / `HOLD_REJECTED` (coordinator verification) and `SUPPLIER_MASTER_REPLACED` / `SUPPLIER_MASTER_REJECTED` documented; `GET /api/audit` is mounted (limitation removed).
- 2026-11-24: events `HOLD_ESCALATED` (a suspected fraud is escalated, never approved), `RECORD_DISPOSED` (retention) and `PRIVACY_SUBJECT_LOOKUP` (habeas data, masked identifier); discard reasons and disposal records are masked with `mask_personal_data` (now in `shared/domain/privacy.py`); `MeteredAuditLog` turns audit events into metrics. Removed the fixed limitation (unmasked discard reasons).
- 2026-11-24: shared Excel sync events `LEDGER_MANUAL_ROW_IMPORTED`, `LEDGER_EDIT_MERGED`, `LEDGER_SYNC_CONFLICT`, `LEDGER_ROW_RESTORED` (`SyncLedger`); test `api/tests/features/ledger/test_excel_sync.py`.
