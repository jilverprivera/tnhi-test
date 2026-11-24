# Auditoría

## Propósito

Un registro de solo escritura de **quién hizo qué, cuándo y sobre qué documento**, y de en qué se diferenció la decisión de la persona de la propuesta del sistema. Responde a la condición principal de Martha —poder ver qué hizo el sistema y por qué— y a la preocupación de la Dra. Herrera sobre quién maneja información sensible.

## Quién lo usa

- **Auxiliar de radicación (CLERK, Martha)**: ve la traza de un documento en su detalle (`GET /api/inbox/{id}` → `audit`).
- **Coordinadora (COORDINATOR, Dra. Herrera)**: lo mismo; supervisa correcciones y aprobaciones, y sus propias liberaciones y rechazos de facturas retenidas quedan auditados (`HOLD_RELEASED` / `HOLD_REJECTED`).
- **Asistente de IA vía MCP**: sin acceso; las herramientas MCP son de solo lectura y no generan eventos.
- **Todo caso de uso que modifica datos**: escribe a través del puerto `AuditLog`.

## Cómo funciona

1. Los casos de uso llaman `audit.record(actor, event, document_id, **details)` después de que el paso de negocio sale bien. El puerto está en `api/app/features/audit/application/ports.py`; el adaptador `SqlAuditLog` (`audit/infrastructure/sql_audit_log.py`) inserta una fila en `audit_events` (`id`, `at` en UTC, `actor`, `event`, `document_id`, `details` JSON).
2. El adaptador **no tiene** métodos para actualizar ni borrar.
3. `ListAudit` devuelve los eventos en orden de inserción, opcionalmente filtrados por documento.
4. El contenedor envuelve el adaptador en `MeteredAuditLog` (`shared/infrastructure/observability.py`): cada evento se escribe igual que antes y algunos además incrementan un contador de Prometheus (ver [observabilidad](observability.md)). Los casos de uso no se enteran.
5. El texto libre que escribe una persona se **enmascara** antes de guardarlo (`mask_personal_data`, `shared/domain/privacy.py`): correos → `[EMAIL]`, cédulas/NIT → `[ID]`, números largos → `[NUMBER]`. El identificador de un titular se reduce a sus últimos 4 caracteres (`mask_identifier`).

Eventos que se registran hoy:

| Evento | Lo escribe | Actor | Detalle |
|---|---|---|---|
| `DOCUMENT_PROPOSED` | `ImportEmails` (por documento) | `SYSTEM` | `status`, `reasons` |
| `EMAILS_IMPORTED` | `ImportEmails` (por lote, `document_id` nulo) | rol que invoca (`CLERK`, `CLI`, `EVALUATION`; en una importación en cola, el actor guardado en ella) | `imported`, `skipped` |
| `DOCUMENT_CORRECTED` | `CorrectDocument` | `CLERK` | `changes` (campo → nuevo valor) |
| `DOCUMENT_DISCARDED` | `DiscardDocument` | `CLERK` | `reason` (enmascarado) |
| `DOCUMENT_APPROVED` | `ApproveDocuments` | `CLERK` / `CLI` | `filing_number`, `action`, `department`, `corrected` |
| `HOLD_ESCALATED` | `EscalateHold` (posible fraude: radicada `ON_HOLD`, `FRAUD_ALERT` a la coordinadora; reemplaza a `DOCUMENT_APPROVED` en las retenidas) | `CLERK` / `CLI` | `filing_number`, `action`, `department`, `corrected` |
| `HOLD_RELEASED` | `VerifyHold` (liberada después de la llamada) | `COORDINATOR` | `filing_number`, `department` |
| `HOLD_REJECTED` | `VerifyHold` (fraude confirmado) | `COORDINATOR` | `filing_number`, `department` |
| `SUPPLIER_MASTER_REPLACED` | `PUT /api/catalogs/suppliers` (`document_id` nulo) | `CLERK` | `suppliers` (cantidad) |
| `SUPPLIER_MASTER_REJECTED` | `PUT /api/catalogs/suppliers` con columnas faltantes (`document_id` nulo) | `CLERK` | `missing_columns` |
| `RECORD_DISPOSED` | `DisposeRecord` (retención, ver [retención documental](records.md); `document_id` nulo para filas históricas) | `COORDINATOR` | `filing_number`, `record_reference` (enmascarado) |
| `LEDGER_MANUAL_ROW_IMPORTED` / `LEDGER_EDIT_MERGED` / `LEDGER_SYNC_CONFLICT` / `LEDGER_ROW_RESTORED` | `SyncLedger` (sincronización del Excel compartido, ver [libro](ledger.md)) | rol que invoca, o `SYSTEM` en aprobaciones y en la sincronización periódica | `filing_number`; `columns` (edición traída) o `column` (conflicto) |
| `PRIVACY_SUBJECT_LOOKUP` | `FindDataSubject` (habeas data, ver [protección de datos](privacy.md); `document_id` nulo) | `COORDINATOR` | `kind`, `identifier` (enmascarado, p. ej. `***.456`), `matches` (cantidad) |

La nota de verificación queda en el `hold_resolution` del ítem de la bandeja y en las marcas del libro, no en el detalle del evento.
Además, la propuesta original se conserva en el ítem de la bandeja (`proposal` nunca se modifica; `GET /api/inbox/{id}` devuelve `proposal_decision` junto a `decision` y `was_corrected`), así que la comparación propuesta-corrección siempre está disponible.

## Reglas de negocio

| Regla | Fuente | Dónde está en el código |
|---|---|---|
| Ella tiene que poder ver qué se hizo y por qué | Martha: *"Que yo pueda ver qué hizo y por qué. No quiero que algo mande las cosas solo y yo no me entere: si se equivoca, la que responde soy yo."* | `DOCUMENT_PROPOSED` con razones; `DOCUMENT_APPROVED` |
| Saber quién ve y maneja los datos | Dra. Herrera: *"La gente de sistemas va a querer saber dónde queda todo eso y quién lo ve."* | actor en cada evento |
| Toda acción que modifica deja evento; se guarda propuesta vs. corrección | Regla del proyecto | llamadas a `record(...)`; `InboxItem.proposal` inmutable |
| Un posible fraude deja un rastro propio: se alerta, nunca se "aprueba" | Decisión del usuario sobre el manejo del fraude | `EscalateHold` → `HOLD_ESCALATED` |
| La auditoría no puede volverse una copia de datos personales | Ley 1581 de 2012; Dra. Herrera: *"les pido cuidado con la información"* | `mask_personal_data` (motivos de descarte, actas de eliminación), `mask_identifier` (búsquedas por titular) |
| La verificación telefónica de la coordinadora sobre una factura retenida queda trazable | Martha: *"se la paso a la doctora Claudia para que verifiquen por teléfono con el proveedor"* | `VerifyHold` → `HOLD_RELEASED` / `HOLD_REJECTED` |

## Endpoints / pantallas

| Método | Ruta | Rol | Solicitud | `code` de éxito |
|---|---|---|---|---|
| GET | `/api/inbox/{id}` | cualquiera | — | `DOCUMENT_FOUND`; `data.audit` trae los eventos del documento |
| GET | `/api/audit` | cualquiera | `document_id` opcional | `AUDIT_LISTED` (todos los eventos, o solo los del documento) |

Forma del evento: `{"at": "...", "actor": "CLERK", "event": "DOCUMENT_APPROVED", "document_id": "01.eml__0", "details": {...}}`.

## Códigos

| Código | Meaning (EN) | Significado (ES) | ¿Bloquea? |
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

## Limitaciones

- El actor es un **rol**, no una persona con nombre (tokens de demostración compartidos); la identidad real requiere SSO.
- Todavía no se auditan los intentos rechazados (p. ej. `DOCUMENT_NEEDS_REVIEW` en la aprobación en lote, `FORBIDDEN`, `HOLD_NOT_PENDING`).
- El evento de aprobación y la fila del libro se escriben en transacciones separadas.
- El enmascaramiento funciona por patrones: los **nombres** de personas escritos en un motivo de descarte no se quitan.
- El "solo escritura" lo garantiza el código (no hay camino para actualizar o borrar), no los permisos de la base de datos.

## Cómo se prueba

- `api/tests/features/audit/test_audit.py`: el adaptador no tiene update/delete/remove; importar + aprobar deja 17 `DOCUMENT_PROPOSED`, `EMAILS_IMPORTED` y `DOCUMENT_APPROVED` con actor `CLERK` y `filing_number` `TAC-2026-ER-04818`.
- `api/tests/features/filing/test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited`.
- `api/tests/features/filing/test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` (`HOLD_REJECTED`).
- `api/tests/api/test_api.py::test_audit_endpoint_and_master_reload_are_audited` (`GET /api/audit` → `AUDIT_LISTED` con `SUPPLIER_MASTER_REJECTED`).
- `HOLD_ESCALATED`: `api/tests/features/filing/test_approve_and_correct.py::test_a_suspected_fraud_is_never_approved_only_escalated`, `api/tests/api/test_api.py::test_approve_rejects_holds_and_escalate_alerts_the_coordinator`.
- `RECORD_DISPOSED`: `api/tests/features/records/test_retention.py::test_dispose_removes_content_and_keeps_the_index`.
- `PRIVACY_SUBJECT_LOOKUP` y motivos de descarte enmascarados: `api/tests/features/privacy/test_subject_requests.py::test_the_audit_never_stores_the_identifier`, `::test_discard_reasons_are_masked_in_the_audit`.

```bash
./scripts/harness-verify.sh api/tests/features/audit/test_audit.py
```

## Historial de cambios

- 2026-11-24: se documentan los eventos `HOLD_RELEASED` / `HOLD_REJECTED` (verificación de la coordinadora) y `SUPPLIER_MASTER_REPLACED` / `SUPPLIER_MASTER_REJECTED`; `GET /api/audit` ya está montado (se retira esa limitación).
- 2026-11-24: eventos `HOLD_ESCALATED` (un posible fraude se alerta, nunca se aprueba), `RECORD_DISPOSED` (retención) y `PRIVACY_SUBJECT_LOOKUP` (habeas data, identificador enmascarado); los motivos de descarte y las actas de eliminación se enmascaran con `mask_personal_data` (ahora en `shared/domain/privacy.py`); `MeteredAuditLog` convierte los eventos de auditoría en métricas. Se quitó la limitación resuelta (motivos de descarte sin enmascarar).
- 2026-11-24: eventos de la sincronización del Excel compartido `LEDGER_MANUAL_ROW_IMPORTED`, `LEDGER_EDIT_MERGED`, `LEDGER_SYNC_CONFLICT`, `LEDGER_ROW_RESTORED` (`SyncLedger`); prueba `api/tests/features/ledger/test_excel_sync.py`.
