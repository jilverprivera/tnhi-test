# 02 — Funcionalidades por rol

Qué puede hacer cada quien y cómo se comprueba. Cada criterio de aceptación apunta a la prueba automática que lo verifica. Detalle técnico por funcionalidad en [../features/](../README.md).

Rutas de pruebas: backend en `api/tests/`, frontend en `web/src/**/__tests__/`, E2E en `web/e2e/`.

## Martha Rojas — auxiliar de radicación (`CLERK`)

### F1. Leer el buzón
Botón "Leer buzón" o carga de `.eml`. Desde la pantalla ambos pasan por la cola de importación (`POST /api/ingestion/jobs/mailbox` / `POST /api/ingestion/jobs/upload` → `202 IMPORT_QUEUED`); el `ImportWorker` en segundo plano convierte los correos en propuestas y la pantalla sigue el trabajo (`GET /api/ingestion/jobs/{id}`) con un aviso de carga, así un pico de fin de mes no bloquea la solicitud. Los endpoints síncronos (`POST /api/ingestion/mailbox`, `POST /api/ingestion/upload`) se mantienen para la CLI y los scripts. Ver [ingesta](../features/ingestion.md).

| Criterio de aceptación | Prueba |
|---|---|
| Cada adjunto es un documento; dos facturas en un correo son dos documentos | `api/tests/features/ingestion/test_split_documents.py::test_every_attachment_is_its_own_document` |
| Si no hay adjuntos, el cuerpo del correo es el documento | `test_split_documents.py::test_body_is_the_document_when_there_are_no_attachments` |
| Las imágenes pequeñas de firma se ignoran | `test_split_documents.py::test_small_signature_images_are_ignored` |
| Un formato no soportado o un adjunto corrupto se marca, no se pierde ni rompe la importación | `test_split_documents.py::test_unsupported_format_is_flagged_not_dropped`, `::test_corrupt_attachment_is_flagged_not_crashing` |
| El buzón de muestra produce 17 documentos | `test_split_documents.py::test_real_mailbox_yields_17_documents` |
| El PDF escaneado pasa por OCR local | `test_split_documents.py::test_scanned_pdf_goes_through_ocr` |
| Las fechas quedan en hora de Bogotá | `test_split_documents.py::test_dates_are_in_bogota_time` |
| Importar dos veces no duplica | `api/tests/features/filing/test_approve_and_correct.py::test_import_is_idempotent` |
| Un trabajo de buzón en cola corre en segundo plano y registra su resultado; los trabajos de carga corren en orden y siguen siendo idempotentes | `api/tests/features/ingestion/test_import_queue.py::test_mailbox_job_runs_and_records_the_result`, `::test_upload_jobs_run_in_order_and_are_idempotent` |
| Un trabajo que falla queda como `FAILED` (`IMPORT_FAILED`) y la cola sigue; un trabajo interrumpido por una caída vuelve a la cola | `test_import_queue.py::test_a_failing_job_is_recorded_and_the_queue_goes_on`, `::test_jobs_interrupted_by_a_crash_go_back_to_the_queue` |
| Por HTTP: `202 IMPORT_QUEUED`, el procesador lo termina con 17 documentos y `GET /api/ingestion/jobs` lo cuenta | `api/tests/api/test_observability.py::test_queued_import_is_processed_by_the_worker` |

### F2. Ver la bandeja con propuesta, motivos y evidencia
Pantalla `/inbox` (filtros pendientes / revisión, 50 documentos por página con "Anterior" / "Siguiente" en la URL, contadores desde `GET /api/inbox/summary`) y `/documents/[id]` ("Por qué"). Ver [bandeja](../features/inbox.md).

| Criterio de aceptación | Prueba |
|---|---|
| Lo que requiere revisión va primero; los motivos bloqueantes salen en español | `web/src/features/inbox/__tests__/mappers.test.ts` |
| En el detalle, los motivos bloqueantes van primero y el campo de cuenta distinta queda resaltado | `web/src/features/document-review/__tests__/mappers.test.ts` |
| Una factura retenida se muestra como "posible fraude", no solo "revisión" | `web/src/shared/ui/__tests__/StatusBadge.test.tsx` |
| Flujo real: la factura sospechosa aparece retenida con el motivo visible | `web/e2e/filing-flow.spec.ts` (paso "the suspicious invoice is held") |
| La bandeja se pagina en SQL (`{items, total, limit, offset}`), filtra por varios estados a la vez y `limit` se limita a 200 | `api/tests/api/test_api.py::test_inbox_and_ledger_are_paginated` |

### F3. Reglas de radicación aplicadas automáticamente
Facturas (maestro, OC, duplicados, fraude), viáticos, derechos de petición, oficios, quejas, cotizaciones y publicidad. Trazabilidad frase → regla → prueba en [03-solucion](03-solucion.md).

| Criterio de aceptación | Prueba |
|---|---|
| 25 reglas de negocio | `api/tests/features/filing/test_rules.py` |
| Plazos en días hábiles colombianos con festivos | `api/tests/shared/test_business_calendar.py` |
| Resultado igual al esperado por el cliente (8/8) y a la tabla completa (17/17) | `api/tests/golden/test_golden.py` |

### F4. Corregir una propuesta
`POST /api/inbox/{id}/correct` (hoja "Corregir": qué es, va para, acción, vencimiento, urgente, observaciones).

| Criterio de aceptación | Prueba |
|---|---|
| La corrección conserva la propuesta original y queda auditada con los campos cambiados | `test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited` |
| Un documento aprobado no se puede corregir | `test_approve_and_correct.py::test_approved_documents_cannot_be_corrected` |
| El formulario rechaza radicar sin dependencia y fechas mal formadas | `web/src/features/document-review/__tests__/mappers.test.ts` ("correction schema") |

### F5. Aprobar y radicar (uno o en lote)
`POST /api/inbox/approve`, `POST /api/inbox/approve-ready`.

| Criterio de aceptación | Prueba |
|---|---|
| El radicado se asigna al aprobar, en orden de llegada (04818…04831) | `test_approve_and_correct.py::test_filing_numbers_are_assigned_on_approval_in_reception_order`, `test_golden.py::test_filing_numbers_continue_the_ledger` |
| "Aprobar listos" solo toma documentos LISTOS | `test_approve_and_correct.py::test_batch_approval_only_takes_ready_documents`, `::test_ready_only_approval_rejects_documents_that_need_review` |
| Un documento ilegible no se puede radicar sin dependencia | `test_approve_and_correct.py::test_unreadable_document_cannot_be_filed_without_a_department` |
| Un posible fraude nunca se aprueba, solo se alerta a la coordinadora (`HOLD_REQUIRES_ESCALATION`, `HOLD_ESCALATED`); "Aprobar listos" se salta las retenidas aunque se hayan corregido a READY | `test_approve_and_correct.py::test_a_suspected_fraud_is_never_approved_only_escalated`, `::test_batch_approval_skips_holds_even_when_corrected_to_ready`, `api/tests/api/test_api.py::test_approve_rejects_holds_and_escalate_alerts_the_coordinator` |
| Dos copias de la misma factura en un lote: la segunda va a revisión | `test_approve_and_correct.py::test_duplicate_inside_the_same_batch_needs_review` |
| Al aprobar se escribe el mensaje en la bandeja de salida (simulado) | `test_approve_and_correct.py::test_approval_writes_simulated_outbox_messages` |
| Flujo real de punta a punta por HTTP | `api/tests/api/test_api.py::test_full_flow_over_http`, `web/e2e/filing-flow.spec.ts` |

### F6. Descartar
`POST /api/inbox/{id}/discard`, con motivo.

| Criterio de aceptación | Prueba |
|---|---|
| Un documento descartado no se puede volver a descartar | `test_approve_and_correct.py::test_discarded_documents_cannot_be_discarded_again` |

### F7. Libro de radicación y Excel
`/ledger`, `GET /api/ledger` (paginado: `limit`, `offset` → `{items, total, limit, offset}`), `GET /api/ledger/export`, `GET /api/ledger/duplicates`. Ver [libro](../features/ledger.md).

| Criterio de aceptación | Prueba |
|---|---|
| Se carga el histórico del Excel del cliente (último 04817) | `api/tests/features/ledger/test_excel_ledger.py::test_ledger_is_seeded_from_the_client_excel` |
| La exportación conserva filas y columnas originales | `test_excel_ledger.py::test_export_keeps_original_rows_and_columns` |
| El original en `material/` nunca se modifica | `test_excel_ledger.py::test_original_material_is_never_modified` |
| Duplicados por proveedor + número; reporta los duplicados históricos 04809/04813 | `test_excel_ledger.py::test_duplicate_lookup_is_by_supplier_and_number`, `::test_historical_duplicates_are_reported` |
| Las filas que escribió Docket se mantienen sincronizadas en el Excel (una factura rechazada dice "Rechazada - fraude confirmado"); la primera sincronización del libro del cliente no cambia nada | `api/tests/features/filing/test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated`, `api/tests/features/ledger/test_excel_sync.py::test_first_sync_changes_nothing` |
| El Excel compartido se sincroniza en ambos sentidos: las filas escritas a mano se importan y la numeración continúa después de ellas; una petición cerrada en el Excel ("Respondido") sale de vencimientos; se conservan las ediciones de la persona y de Docket en la misma fila; misma celda en ambos lados → gana la persona y se registra un conflicto; una fila borrada se restaura; un Excel abierto nunca se sobrescribe; un guardado durante la fusión se vuelve a fusionar | `api/tests/features/ledger/test_excel_sync.py` (8 escenarios) |
| Los filtros usan el select del sistema de diseño; "ALL" significa sin filtro | `web/src/shared/ui/__tests__/FilterSelect.test.tsx`, `web/src/features/ledger/__tests__/mappers.test.ts`, `web/e2e/coordinator.spec.ts` (último paso) |
| El libro se pagina (28 filas históricas: la página `offset=20, limit=10` trae 8) y los enlaces de página conservan la búsqueda | `test_api.py::test_inbox_and_ledger_are_paginated`, `web/src/features/ledger/__tests__/mappers.test.ts` ("keep the search and move the offset") |

### F8. Configuración: maestro de proveedores y dependencias
`/settings`, `PUT /api/catalogs/suppliers`.

| Criterio de aceptación | Prueba |
|---|---|
| Búsqueda por NIT y por dominio | `api/tests/features/catalogs/test_catalogs.py::test_master_lookup_by_nit_and_domain` |
| Un maestro inválido se rechaza y se conserva el anterior | `test_catalogs.py::test_invalid_master_upload_is_rejected_and_keeps_the_old_one` |
| El reemplazo del maestro queda auditado | `test_api.py::test_audit_endpoint_and_master_reload_are_audited` |

## Dra. Claudia Herrera — coordinadora (`COORDINATOR`)

### F9. Vencimientos de la semana e informe semanal
`/deadlines` (pantalla de inicio de la coordinadora), `GET /api/deadlines`, `GET /api/deadlines/weekly-report`.

| Criterio de aceptación | Prueba |
|---|---|
| Estados: vencido, hoy, esta semana, próxima semana, después | `api/tests/features/deadlines/test_deadlines.py::test_week_bounds_and_states` |
| El informe incluye documentos aún no radicados (sin esperar a Martha) | `test_deadlines.py::test_weekly_report_includes_documents_not_filed_yet` |
| Los radicados conservan su urgencia | `test_deadlines.py::test_filed_deadlines_keep_their_urgency` |
| Días hábiles restantes en español; "sin radicar" marcado | `web/src/features/deadlines/__tests__/mappers.test.ts` |
| Flujo real: la coordinadora ve los vencimientos y no puede aprobar | `web/e2e/filing-flow.spec.ts` (último paso) |

### F10. Consultar todo; la radicación sigue siendo de Martha

| Criterio de aceptación | Prueba |
|---|---|
| Sin token no hay acceso | `test_api.py::test_requires_a_token` |
| La coordinadora no puede aprobar (`FORBIDDEN`) | `test_api.py::test_coordinator_cannot_approve` |
| Puede consultar la auditoría | `test_api.py::test_audit_endpoint_and_master_reload_are_audited` |

### F11. Uso en teléfono e instalación (PWA)

| Criterio de aceptación | Prueba |
|---|---|
| Barra de pestañas inferior, sin scroll horizontal, manifiesto instalable (`standalone`) | `web/e2e/mobile.spec.ts` |

### F12. Verificar las facturas retenidas por posible fraude
`/verifications` ("Por verificar"), `GET /api/verifications`, `POST /api/verifications/{id}/release`, `POST /api/verifications/{id}/reject` (cuerpo `{"note"}`). Entrevista: Martha "se la paso a la doctora Claudia para que verifiquen por teléfono con el proveedor". Cada tarjeta pone lo que llegó al lado del maestro de proveedores (cuenta bancaria, correo del remitente) con la diferencia marcada; después de la llamada, ella libera la factura o confirma el fraude, con una nota obligatoria.

| Criterio de aceptación | Prueba |
|---|---|
| La factura retenida espera a la coordinadora cuando Martha la alerta ("Alertar a la Dra. Herrera"); antes sigue en radicación y no se puede resolver | `api/tests/features/filing/test_verify_hold.py::test_held_invoice_waits_for_the_coordinator`, `::test_before_martha_approves_it_is_still_with_the_clerk` |
| Liberarla la envía a donde la habría mandado la regla de orden de compra de Martha (libro `DELIVERED`, marca `VERIFIED_BY_PHONE`, `FORWARD_TO_DEPARTMENT` en la bandeja de salida) | `test_verify_hold.py::test_release_sends_it_where_the_rules_would_have` |
| Rechazarla marca el libro `REJECTED` (`FRAUD_CONFIRMED`) y avisa a Cuentas por pagar y a Compras | `test_verify_hold.py::test_reject_marks_fraud_and_warns_payables_and_procurement` |
| La nota es obligatoria y una retención no se resuelve dos veces | `test_verify_hold.py::test_cannot_resolve_twice_or_without_a_note` |
| La resolución queda auditada y la fila del Excel se actualiza | `test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` |
| Solo la coordinadora resuelve (`FORBIDDEN` para Radicación; `VERIFICATION_NOTE_REQUIRED`, `HOLD_NOT_PENDING`) | `api/tests/api/test_api.py::test_only_the_coordinator_resolves_held_invoices` |
| La tarjeta compara lo que llegó con el maestro, marca ambas diferencias, distingue proveedores no registrados y agrupa según quién debe actuar | `web/src/features/verifications/__tests__/mappers.test.ts` |
| Flujo real: Martha alerta a la Dra. Herrera sobre la factura sospechosa ("Enviar alerta"), la Dra. Herrera compara, la libera hacia Cuentas por pagar y el libro la muestra entregada | `web/e2e/coordinator.spec.ts` |

### F13. Su propio espacio de trabajo
Menú según el rol (Vencimientos, Por verificar, Libro, Bandeja, Cumplimiento) e inicio (`/deadlines`, donde un resumen muestra las facturas por verificar y lo pendiente en radicación); la bandeja se abre en modo de supervisión, solo lectura.

| Criterio de aceptación | Prueba |
|---|---|
| Al ingresar llega a su inicio con su propio menú; el menú de Radicación no tiene "Por verificar" | `web/e2e/coordinator.spec.ts` (pasos 1–2) |
| La pantalla de vencimientos le muestra la tarjeta "1 factura por verificar", que lleva a `/verifications` | `web/e2e/coordinator.spec.ts` (paso 2) |

### F14. Retención documental (Ley 594 de 2000)
`/compliance` ("Cumplimiento"), `GET /api/retention/schedule`, `GET /api/retention?status=&on=&limit=&offset=`, `POST /api/retention/{filing_number}/dispose` (cuerpo `{"record_reference"}`, solo COORDINATOR). La Tabla de Retención Documental (TRD) por tipo documental es una propuesta inicial que debe aprobar el Comité Interno de Archivo de TAC; los tiempos cuentan desde el cierre del año en que se recibió el documento. La eliminación borra el archivo original y el texto extraído, pero conserva la fila del libro como índice (marca `DISPOSED`, nota en el Excel "Eliminado según la Tabla de Retención Documental"). Ver [records](../features/records.md) y [compliance](../features/compliance.md).

| Criterio de aceptación | Prueba |
|---|---|
| Los soportes contables (facturas) se conservan 10 años desde el cierre del año (04818 → 2036-12-31) | `api/tests/features/records/test_retention.py::test_accounting_support_is_kept_ten_years_from_year_end` |
| En la fecha del caso nada ha cumplido su retención; también se cubren las filas históricas (28 + 3 radicadas) | `test_retention.py::test_nothing_is_due_today`, `::test_historical_rows_are_covered_too` |
| La eliminación borra el contenido, conserva el índice y la decisión, escribe la nota en el Excel y el evento `RECORD_DISPOSED` | `test_retention.py::test_dispose_removes_content_and_keeps_the_index` |
| Nunca antes de tiempo (`RETENTION_NOT_EXPIRED`) y nunca lo que debe conservarse (`DISPOSITION_NOT_ALLOWED`) | `test_retention.py::test_never_before_the_term_and_never_what_must_be_conserved` |
| La fecha de consulta solo acepta fechas ISO; toda disposición final tiene etiqueta en español | `web/src/features/compliance/__tests__/labels.test.ts` |
| Flujo real: la coordinadora abre "Cumplimiento" y ve la TRD y que nada ha cumplido su retención | `web/e2e/coordinator.spec.ts` ("compliance: retention schedule and a data subject request") |

### F15. Solicitudes de titulares (habeas data, Ley 1581 de 2012)
`/compliance`, `GET /api/privacy/inventory` (inventario de datos personales y salvaguardas), `POST /api/privacy/subject-requests` (cuerpo `{"identifier", "kind"}`, solo COORDINATOR). Con una cédula o un correo, lista dónde están los datos de esa persona (libro y bandeja) y el plazo legal para responder: consulta (`INQUIRY`, art. 14) 10 días hábiles, reclamo (`CLAIM`, art. 15) 15 días hábiles. Ver [privacy](../features/privacy.md).

| Criterio de aceptación | Prueba |
|---|---|
| Encuentra a un empleado por cédula en la bandeja y en el libro; una consulta vence en 10 días hábiles | `api/tests/features/privacy/test_subject_requests.py::test_finds_an_employee_by_national_id` |
| Encuentra a un ciudadano por correo; un reclamo vence en 15 días hábiles (se salta el festivo del 8 de diciembre) | `test_subject_requests.py::test_finds_a_citizen_by_email_and_claims_have_15_days` |
| La auditoría (`PRIVACY_SUBJECT_LOOKUP`) nunca guarda el identificador, solo uno enmascarado | `test_subject_requests.py::test_the_audit_never_stores_the_identifier` |
| Se rechazan identificadores demasiado cortos (`IDENTIFIER_TOO_SHORT`) | `test_subject_requests.py::test_too_short_identifiers_are_rejected` |
| Solo la coordinadora hace la consulta y el identificador viaja en el cuerpo, nunca en la URL | `test_subject_requests.py::test_only_the_coordinator_runs_subject_requests_and_ids_travel_in_the_body` |
| Flujo real: busca "80.123.456" y ve "Titular ***.456" y el plazo para responder | `web/e2e/coordinator.spec.ts` ("compliance: retention schedule and a data subject request") |

## Asistente de IA por MCP (en nombre de la Dra. Herrera)

Herramientas: `deadlines_this_week`, `weekly_report`, `list_deadlines`, `search_ledger`, `pending_review`, `held_invoices`, `inbox_summary`. Ver [mcp](../features/mcp.md).

| Criterio de aceptación | Prueba |
|---|---|
| Responde "¿qué vence esta semana?" | `api/tests/mcp/test_mcp_server.py::test_what_is_due_this_week` |
| Un rango de fechas incluye documentos aún no radicados | `test_mcp_server.py::test_deadlines_in_a_range_include_unfiled_documents` |
| Busca en el libro y lista lo pendiente de revisión | `test_mcp_server.py::test_search_ledger_and_pending_review` |
| Lista las facturas retenidas con su estado de verificación y los motivos de fraude | `test_mcp_server.py::test_held_invoices_tool` |
| Ninguna herramienta modifica estado | `test_mcp_server.py::test_tools_are_read_only` |

## Transversales

| Criterio de aceptación | Prueba |
|---|---|
| Toda acción que modifica deja un evento de auditoría; la auditoría es de solo agregar | `api/tests/features/audit/test_audit.py` |
| La IA está apagada por defecto, solo se consulta si las reglas dudan, recibe datos enmascarados y sus negativas vuelven a las reglas | `api/tests/features/classification/test_assisted_classifier.py` |
| Los motivos de descarte en texto libre se enmascaran antes de llegar a la auditoría | `api/tests/features/privacy/test_subject_requests.py::test_discard_reasons_are_masked_in_the_audit` |
| Monitoreo: `GET /metrics` expone conteos del negocio (propuestas, motivos, aprobaciones, duración de importación) sin datos personales; se devuelve el `X-Request-ID`; `GET /api/ready` responde `READY` con las verificaciones de base de datos y procesador. Ver [observability](../features/observability.md) | `api/tests/api/test_observability.py::test_metrics_expose_business_counts_without_personal_data`, `::test_request_id_and_readiness` |
| Con documentos escritos por alguien que nunca vio el código, el resultado no baja de la línea base ciega (≥ 45/65 correctos, ≤ 6 errados) y ninguna retención por fraude ni duplicado se pierde en silencio. Ver [evaluation](../features/evaluation.md) | `api/tests/blind/test_blind_baseline.py` |
| Respuestas y errores con códigos `UPPER_SNAKE_CASE` | `test_api.py::test_responses_use_the_upper_snake_case_envelope`, `::test_validation_errors_are_upper_snake_case`, `::test_unknown_document_returns_a_code` |
