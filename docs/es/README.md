# Docket — documentación (español)

Docket hace el trabajo de radicación de Terminales Andinas de Carga (TAC) sobre el buzón de radicación: lee los correos y sus adjuntos, clasifica cada documento, aplica las reglas de la auxiliar, propone dependencia / acción / fecha de vencimiento y —solo cuando la auxiliar aprueba— continúa el libro de radicación en Excel del cliente con los consecutivos `TAC-2026-ER-#####`. Un servidor MCP de solo lectura le permite a un asistente de IA responder "¿qué se vence esta semana?".

Versión en inglés: [../en/README.md](../en/README.md).

## Entregables

Documentos de la entrevista, en `deliverables/`. Empiece por el resumen ejecutivo.

| Documento | Qué responde |
|---|---|
| [00 — Resumen ejecutivo](deliverables/00-resumen-ejecutivo.md) | Componentes y dónde interviene la IA, cómo se sabe que acierta, costo, tiempo ahorrado, deuda técnica (2–3 páginas, un diagrama) |
| [01 — Arquitectura](deliverables/01-arquitectura.md) | C4, slices y regla hexagonal, frontend, flujo de datos, despliegue, dónde queda cada dato y quién lo ve |
| [02 — Funcionalidades](deliverables/02-features.md) | Funcionalidades por rol con criterios de aceptación ligados a pruebas |
| [03 — Solución](deliverables/03-solucion.md) | Trazabilidad frase de Martha → regla → código → prueba; resultado de la bandeja; decisiones de criterio |
| [04 — Modelo de dominio](deliverables/04-modelo-dominio.md) | Entidades, enumeraciones y ciclo de vida del documento |
| [05 — Atributos de calidad](deliverables/05-atributos-calidad.md) | Escenarios ISO 25010 con medida, verificación y brechas |

## Funcionalidades del backend

| Funcionalidad | Qué cubre |
|---|---|
| [Ingesta](features/ingestion.md) | Importación de correos `.eml`, separación en documentos, extracción de texto y OCR local; cola de importación persistente con procesador en segundo plano para los picos de fin de mes |
| [Clasificación](features/classification.md) | Tipo de documento y extracción de datos; segunda opinión con IA opcional (apagada por defecto) |
| [Radicación](features/filing.md) | Reglas de negocio, códigos de razón, revisión, corrección, aprobación, radicados, bandeja de salida, verificación de facturas retenidas |
| [Libro de radicación](features/ledger.md) | El Excel del cliente sincronizado en ambos sentidos con el archivo compartido, numeración, búsqueda paginada, exportación, duplicados |
| [Vencimientos](features/deadlines.md) | Plazos en días hábiles, estados de vencimiento, informe semanal de la coordinadora |
| [Catálogos](features/catalogs.md) | Maestro de proveedores y dependencias |
| [Auditoría](features/audit.md) | Registro de solo escritura de quién hizo qué, con los datos personales enmascarados |
| [Retención documental](features/records.md) | Tabla de retención documental (TRD, Ley 594 de 2000), registros que cumplieron su retención, eliminación controlada que conserva el índice |
| [Protección de datos personales](features/privacy.md) | Habeas data (Ley 1581 de 2012): inventario de datos personales, búsqueda por titular con plazos legales, enmascaramiento compartido |
| [Observabilidad](features/observability.md) | Métricas de Prometheus en `/metrics`, disponibilidad `GET /api/ready`, registros JSON con `X-Request-ID` |
| [Evaluación](features/evaluation.md) | Tabla dorada (8/8, 17/17) y set ciego (45/65 correctos, 14 a una persona, 6 errores); política de no ajustar |
| [Servidor MCP](features/mcp.md) | Herramientas de solo lectura para un asistente de IA |

## Funcionalidades del frontend

Pantallas de la aplicación web (`web/`, Next.js). Las pantallas del libro y de vencimientos están en el mismo documento de su módulo del backend (comparten slug).

| Funcionalidad | Qué cubre |
|---|---|
| [Bandeja](features/inbox.md) | La cola de la auxiliar: importación de correo en cola, filtros, contadores, paginación, aprobación en lote de lo `READY` |
| [Revisión de documento](features/document-review.md) | Un documento: original, propuesta, motivos, datos, historial; aprobar, corregir, descartar; alertar a la coordinadora de un posible fraude |
| [Verificaciones](features/verifications.md) | `/verifications`: las facturas retenidas de la coordinadora, lo que llegó frente al maestro de proveedores, liberar o confirmar fraude (backend en el slice de radicación) |
| [Libro](features/ledger.md#la-pantalla-ledger) | `/ledger`: búsqueda, alerta de duplicados históricos, tabla/tarjetas, descarga del Excel |
| [Vencimientos](features/deadlines.md#la-pantalla-deadlines) | `/deadlines`: informe semanal para la coordinadora, impresión, consulta sin conexión |
| [Ajustes](features/settings.md) | Estado del sistema (disponibilidad, cola de importación), estado de la IA, maestro de proveedores (y su reemplazo), dependencias, bandeja de salida simulada |
| [Cumplimiento](features/compliance.md) | `/compliance`: tabla de retención de la coordinadora, registros por eliminar, inventario de datos personales y solicitudes de titulares |
| [Sesión y marco de la aplicación](features/session.md) | Ingreso, cookie httpOnly con el token, protección de rutas, encabezado, barra lateral y de pestañas, roles en la pantalla |
| [PWA](features/pwa.md) | Manifiesto, íconos, instalación, service worker con Serwist, qué se guarda (y qué no) sin conexión |

## Roles

| Rol | Persona | Puede |
|---|---|---|
| `CLERK` | Martha Rojas, auxiliar de radicación | importar, corregir, descartar, aprobar, alertar a la coordinadora de un posible fraude, reemplazar el maestro de proveedores, consultar todo |
| `COORDINATOR` | Dra. Claudia Herrera, coordinadora administrativa y financiera | liberar o rechazar facturas retenidas después de llamar al proveedor, eliminar registros que cumplieron su retención, hacer búsquedas por titular, consultar todo (bandeja, libro, vencimientos, bandeja de salida) |
| Asistente de IA (MCP) | en nombre de cualquiera de las dos | herramientas de solo lectura |

Convenciones de la API: toda respuesta es `{"code": "UPPER_SNAKE", "data": ...}`; los errores, `{"code": "...", "detail": {...}}`. Autenticación con `Authorization: Bearer <token>` (`TAC_CLERK_TOKEN`, por defecto `martha-demo`; `TAC_COORDINATOR_TOKEN`, por defecto `herrera-demo`). Los códigos van en inglés; la interfaz los traduce al español.

## Cómo ejecutar el backend

Desde la raíz del repositorio (en `material/` nunca se escribe; los datos van a `api/data/` o al directorio que se indique):

```bash
cd api
uv sync                                               # instala dependencias
uv run uvicorn app.main:app --reload                  # API REST en http://localhost:8000 (documentación en /docs)
uv run python -m app.cli process --data-dir /tmp/docket --approve-all   # todo el buzón de punta a punta; imprime las propuestas
uv run python -m app.mcp.server                       # servidor MCP de solo lectura (stdio); con --http en :8001
```

Pruebas — nunca se corre toda la suite de una vez; se usa el harness desde la raíz del repositorio:

```bash
./scripts/harness-verify.sh --backend                 # ruff + lotes de pytest de los módulos cambiados
./scripts/harness-verify.sh api/tests/golden/test_golden.py   # archivos puntuales
```

Configuración (`TAC_*`, ver `api/app/shared/config.py` y el comentado `api/.env.example`). **Nada tiene valor por defecto en el código:** cada ajuste es su variable o queda indefinido. Los obligatorios (`TAC_DATA_DIR`, `TAC_DATABASE_URL`, `TAC_INBOX_DIR`, `TAC_SUPPLIERS_CSV`, `TAC_DEPARTMENTS_CSV`, `TAC_LEDGER_XLSX`, `TAC_COMPANY_NIT`, `TAC_FILING_PREFIX`, `TAC_OCR_LANGUAGE`, `TAC_MIN_OCR_CONFIDENCE`, `TAC_MIN_CLASSIFICATION_MARGIN`, más `TAC_WORKER_POLL_SECONDS` con el procesador encendido y `TAC_MCP_HOST`/`TAC_MCP_PORT` para MCP por HTTP) fallan con `MissingSettingError: TAC_<NOMBRE> is not set`. Los opcionales significan "apagado" si no están: `TAC_TODAY` (fecha real), `TAC_CLERK_TOKEN`/`TAC_COORDINATOR_TOKEN` (ese rol no puede entrar), `TAC_CORS_ORIGINS` (sin CORS), `TAC_LLM_ENABLED`+`TAC_ANTHROPIC_API_KEY`+`TAC_LLM_MODEL` (IA solo con los tres), `TAC_WORKER_ENABLED`, `TAC_LEDGER_SYNC_SECONDS` (solo al aprobar, exportar o a demanda), `TAC_EXTRA_HOLIDAYS`. El API lee `api/.env` sin importar desde dónde se inicie, y las rutas relativas se resuelven desde `api/`. La web solo necesita `DOCKET_API_URL`; la fecha del caso viene del API. Los PDF escaneados necesitan Tesseract con el idioma español (`tesseract-ocr`, `tesseract-ocr-spa`); sin él pasan a revisión humana como `DOCUMENT_UNREADABLE`.
