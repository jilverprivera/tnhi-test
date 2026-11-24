# 05 — Atributos de calidad (ISO/IEC 25010)

Cada escenario sigue la forma fuente → estímulo → entorno → respuesta → medida, con cómo se verifica hoy y qué falta. Cifras medidas en la imagen Docker de la API con el buzón de muestra.

## 1. Adecuación funcional — corrección

| | |
|---|---|
| **Fuente** | Un correo del buzón de radicación |
| **Estímulo** | Martha pulsa "Leer buzón" |
| **Entorno** | Operación normal, maestro y libro cargados, OCR disponible |
| **Respuesta** | Cada documento recibe tipo, dependencia, acción y vencimiento según las reglas de la entrevista |
| **Medida** | 8/8 en los resultados esperados del cliente; 17/17 en la tabla completa; márgenes del clasificador ≥ 2; set ciego (65 documentos que nunca se usaron para ajustar las reglas): 45 correctos, 14 enviados a una persona, 6 errados, todas las retenciones por fraude y los duplicados detectados ([evaluación](../features/evaluation.md)) |
| **Cómo se verifica hoy** | `api/tests/golden/test_golden.py` (debe estar al 100 %), `api/tests/features/filing/test_rules.py` (25 reglas), `api/tests/shared/test_business_calendar.py`, `api/tests/blind/test_blind_baseline.py` (piso: ≥ 45 correctos, ≤ 6 errados) |
| **Brecha** | El set ciego es sintético (escrito a partir de la entrevista, no es correo real de TAC); siguen abiertos los 6 errores del set ciego; aún no se mide la tasa de corrección por tipo en producción |

## 2. Seguridad — trazabilidad y auditabilidad (responsabilidad, no repudio)

| | |
|---|---|
| **Fuente** | Contabilidad, Jurídica o un auditor |
| **Estímulo** | Pregunta "¿quién radicó esto, qué propuso el sistema y qué cambió una persona?" |
| **Entorno** | Cualquier momento después de la aprobación |
| **Respuesta** | La auditoría muestra importación, propuesta, corrección (campos cambiados), aprobación, descarte y la resolución de la coordinadora sobre una factura retenida (`HOLD_RELEASED` / `HOLD_REJECTED`, con su nota en el libro); la propuesta original se conserva junto a la decisión final |
| **Medida** | 100 % de las acciones que modifican estado dejan un evento; 0 endpoints de edición o borrado de la auditoría |
| **Cómo se verifica hoy** | `api/tests/features/audit/test_audit.py`, `test_approve_and_correct.py::test_correction_keeps_the_original_proposal_and_is_audited`, `test_api.py::test_audit_endpoint_and_master_reload_are_audited`, `test_verify_hold.py::test_resolution_is_audited_and_the_excel_row_is_updated` |
| **Brecha** | El actor es el rol (`CLERK`), no la persona (requiere SSO); las aprobaciones rechazadas no se auditan; la auditoría vive en la misma BD (no hay sellado externo) |

## 3. Seguridad — confidencialidad y privacidad

| | |
|---|---|
| **Fuente** | Sistemas de TAC / un usuario no autorizado |
| **Estímulo** | "¿Dónde quedan los datos de personas, contratos y pagos y quién los ve?" / intento de acceso sin token o con el rol equivocado |
| **Entorno** | Despliegue on-prem |
| **Respuesta** | Todo queda en el servidor de TAC; OCR local; IA apagada; motivos de descarte en texto libre enmascarados en la auditoría; consultas de titulares auditadas con el identificador enmascarado, y el identificador viaja en el cuerpo, nunca en la URL; los documentos que cumplieron su retención se eliminan con acta aprobada (se borra el contenido, queda el índice en el libro); las métricas solo llevan conteos; sin token → 401; la coordinadora no puede aprobar → 403; Radicación no puede resolver una factura retenida → 403; token en cookie httpOnly; MCP de solo lectura ligado a localhost |
| **Medida** | 0 bytes de documentos fuera de TAC con la configuración por defecto; 100 % de endpoints que modifican exigen un rol: `CLERK`, salvo resolver facturas retenidas, que exige `COORDINATOR` |
| **Cómo se verifica hoy** | `test_api.py::test_requires_a_token`, `::test_coordinator_cannot_approve`, `::test_only_the_coordinator_resolves_held_invoices`, `test_assisted_classifier.py::test_disabled_by_default`, `::test_personal_data_is_masked_before_leaving_tac`, `test_mcp_server.py::test_tools_are_read_only`, `test_subject_requests.py` (identificador enmascarado, motivos de descarte enmascarados, solo la coordinadora), `test_retention.py`, `test_observability.py::test_metrics_expose_business_counts_without_personal_data`; ver [privacy](../features/privacy.md) y [records](../features/records.md) |
| **Brecha** | Tokens de demo en lugar de SSO; sin cifrado en reposo; MCP sin autenticación; los valores de la Tabla de Retención Documental (TRD) esperan la aprobación del Comité Interno de Archivo de TAC; la IA requiere aprobación de Sistemas (DPA, región de datos) |

## 4. Usabilidad

| | |
|---|---|
| **Fuente** | Martha (18 años en el cargo, no técnica) o la Dra. Herrera desde el teléfono |
| **Estímulo** | Radicar el represamiento desde el 10-nov sin ayuda del desarrollador |
| **Entorno** | Escritorio o teléfono, en español |
| **Respuesta** | Bandeja con lo que requiere revisión primero, "Por qué" con motivos y evidencia en español, corrección en una hoja, "Aprobar listos" en lote, Excel descargable; controles de al menos 44 px de alto en pantallas táctiles; si una vista no carga, una página ofrece "Reintentar" o "Ingresar de nuevo"; en teléfono, barra de pestañas inferior e instalación como PWA |
| **Medida** | Flujo completo (leer, revisar, corregir, aprobar, exportar, ver vencimientos) sin salir de la app; 0 scroll horizontal en teléfono |
| **Cómo se verifica hoy** | `web/e2e/filing-flow.spec.ts`, `web/e2e/mobile.spec.ts`, pruebas de mappers en `web/src/features/*/__tests__/` |
| **Brecha** | No hay prueba con Martha cronometrada; falta auditoría formal de accesibilidad (WCAG AA) |

### Vistas según el rol

| | |
|---|---|
| **Fuente** | La Dra. Herrera (coordinadora), que supervisa y verifica pero no radica |
| **Estímulo** | Ingresa para ver qué la espera y resolver una factura retenida por posible fraude |
| **Entorno** | Escritorio o teléfono, en español, después de que Martha alertó sobre la factura retenida ("Alertar a la Dra. Herrera") |
| **Respuesta** | Al ingresar, cada rol llega a su propio inicio (`ROLE_HOME`: Radicación `/inbox`, Coordinación `/deadlines`) con su propio menú (`ROLE_NAV`); su pantalla de vencimientos abre con las "facturas por verificar" y lo pendiente en radicación; "Por verificar" pone lo que llegó al lado del maestro de proveedores (cuenta bancaria, correo del remitente) con la diferencia marcada, y un diálogo con nota obligatoria para liberar o confirmar el fraude; la bandeja se abre en modo de supervisión, solo lectura |
| **Medida** | Del ingreso a una factura retenida resuelta en 3 clics más la nota, sin salir de la app; Radicación nunca ve "Por verificar" y la coordinadora nunca ve botones de radicación |
| **Cómo se verifica hoy** | `web/e2e/coordinator.spec.ts`, `web/src/features/verifications/__tests__/mappers.test.ts`, `test_api.py::test_only_the_coordinator_resolves_held_invoices` |
| **Brecha** | No se ha validado con la Dra. Herrera; no hay notificación (correo o push) cuando una factura nueva espera verificación: la ve cuando abre la app o le pregunta al asistente por MCP (`held_invoices`) |

## 5. Eficiencia de desempeño

| | |
|---|---|
| **Fuente** | Martha |
| **Estímulo** | Lee el buzón de un día (≈ 40 documentos) o de una semana represada |
| **Entorno** | Servidor on-prem, un proceso |
| **Respuesta** | Propuestas listas para revisar |
| **Medida** | Mediana 20 ms por PDF nativo o cuerpo (máx. 50 ms); escaneado con OCR 1,9 s; buzón de 17 documentos 2,2 s; aprobar todo 0,2 s. Una importación de fin de mes queda en cola (`202 IMPORT_QUEUED`) y responde de inmediato mientras el procesador en segundo plano la trabaja; las páginas de bandeja y libro tienen máximo 200 filas (50 por defecto), y la bandeja se pagina en SQL |
| **Cómo se verifica hoy** | Medición manual en la imagen Docker (CLI `app.cli process`); `test_import_queue.py`, `test_observability.py::test_queued_import_is_processed_by_the_worker`, `test_api.py::test_inbox_and_ledger_are_paginated`; duración de cada trabajo en la métrica `docket_import_job_seconds` |
| **Brecha** | Sin prueba de carga automatizada; un solo hilo procesador por proceso de la API; el candado de numeración es en proceso (no es seguro con varios procesos de la API); el libro y la lista de retención se filtran en memoria antes de paginar |

## 6. Mantenibilidad — reglas como código, slices

| | |
|---|---|
| **Fuente** | Desarrollador o la abogada |
| **Estímulo** | Cambia una regla (p. ej. un plazo, un festivo, una nueva dependencia) |
| **Entorno** | Desarrollo |
| **Respuesta** | El cambio se hace en un solo lugar (`filing/domain/rules.py`, `TAC_EXTRA_HOLIDAYS`, maestro o dependencias), con su prueba; el dominio no depende de frameworks |
| **Medida** | Un cambio de regla toca 1 archivo de dominio + 1 prueba; la tabla de oro detecta regresiones |
| **Cómo se verifica hoy** | Pruebas por slice en `api/tests/features/`, regla de dependencias `domain <- application <- infrastructure/api` (ver [01-arquitectura](01-arquitectura.md)) |
| **Brecha** | Las reglas están en código, no en una tabla editable por el negocio; sin verificación automática de la regla de dependencias (p. ej. import-linter) |

## 7. Portabilidad — on-prem o nube

| | |
|---|---|
| **Fuente** | Sistemas de TAC |
| **Estímulo** | Instalar en un servidor propio o en la nube |
| **Entorno** | Linux con Docker |
| **Respuesta** | `docker compose up --build` levanta web y API con SQLite en un volumen; la misma imagen corre en Render con disco (`render.yaml`) y la web en Vercel |
| **Medida** | 1 comando; configuración solo por variables `TAC_*` |
| **Cómo se verifica hoy** | Imágenes construidas y probadas localmente (OCR verificado dentro de la imagen) |
| **Brecha** | La demo en la nube no está desplegada todavía; Postgres soportado pero no probado en esta entrega |

## 8. Fiabilidad — disponibilidad y trabajo sin conexión

| | |
|---|---|
| **Fuente** | Falla de internet o del proveedor de IA |
| **Estímulo** | No hay salida a internet / la API de Claude no responde o se niega |
| **Entorno** | On-prem |
| **Respuesta** | La radicación sigue funcionando: no depende de la nube; si la IA falla o se niega, se vuelve a las reglas; la PWA muestra una página sin conexión y conserva vistas de lectura. Operación lo puede vigilar: métricas Prometheus en `/metrics`, `/api/ready` (`READY` 200 / `NOT_READY` 503; si falta el OCR solo queda degradado), logs JSON con `X-Request-ID`; un trabajo interrumpido por una caída vuelve a la cola al reiniciar |
| **Medida** | 0 dependencias externas en la ruta por defecto |
| **Cómo se verifica hoy** | `test_assisted_classifier.py::test_refusals_fall_back_to_rules`, `::test_disabled_by_default`; ruta `/offline` de la PWA; `test_observability.py::test_request_id_and_readiness`, `test_import_queue.py::test_jobs_interrupted_by_a_crash_go_back_to_the_queue`; ver [observability](../features/observability.md) |
| **Brecha** | Un solo servidor, sin réplica; hay métricas, pero no se entregan reglas de alerta ni tableros; sin copias de seguridad automatizadas |

### Integridad del Excel compartido

| | |
|---|---|
| **Fuente** | Contabilidad, Jurídica o Martha trabajando sobre el Excel compartido mientras Docket radica |
| **Estímulo** | Alguien escribe una fila a mano, pone "Respondido" en un estado, agrega una nota, borra una fila o tiene el archivo abierto mientras Docket aprueba |
| **Entorno** | Operación normal; el libro en una carpeta compartida |
| **Respuesta** | `SyncLedger` fusiona en ambos sentidos, celda por celda: las filas escritas a mano se importan y la numeración continúa después de ellas; las ediciones de las personas entran al libro (una petición cerrada sale de vencimientos); misma celda cambiada en ambos lados → gana la persona y el conflicto se muestra en `/ledger`; una fila borrada se restaura; el archivo nunca se escribe mientras está abierto (`LOCKED`, se escribe después) ni si cambió durante la fusión (se fusiona otra vez, reemplazo atómico) |
| **Medida** | 0 celdas escritas por personas perdidas; 0 radicados repetidos o faltantes; 0 escrituras sobre un archivo abierto |
| **Cómo se verifica hoy** | `api/tests/features/ledger/test_excel_sync.py` (8 escenarios); ver [ledger](../features/ledger.md#sincronización-en-ambos-sentidos-con-el-excel-compartido) |
| **Brecha** | El libro es un archivo en una carpeta local o montada: falta un adaptador para SharePoint / Google Drive; la detección de bloqueo depende del archivo `~$` de Excel; el candado de numeración y la sincronización son de un solo proceso |

## 9. Costo

| | |
|---|---|
| **Fuente** | Dirección administrativa y financiera |
| **Estímulo** | 200 documentos por semana (≈ 870/mes) |
| **Entorno** | Producción on-prem |
| **Respuesta** | Ruta de reglas sobre CPU propia; IA solo si se habilita y solo para ambiguos |
| **Medida** | ≈ US$ 0 marginal con reglas; ≈ US$ 0,01/mes con Haiku 5.5 para el 20 % ambiguo; ≈ US$ 0,91/mes con Sonnet 5.5 para todo (precios a verificar) |
| **Cómo se verifica hoy** | Cálculo con ≈ 500 tokens de entrada + 5 de salida por llamada; ver [00-resumen-ejecutivo](00-resumen-ejecutivo.md#c-cuánto-cuesta-procesar-un-documento) |
| **Brecha** | No se registra el consumo real de tokens; costo de la demo en la nube por confirmar en la página de precios de cada proveedor |
