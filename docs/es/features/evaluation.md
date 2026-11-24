# Evaluación (tabla dorada y set ciego)

## Propósito

Responde "¿cómo sabemos que Docket acierta?" con cifras que se pueden reproducir. Docket se mide contra dos tipos de referencia: la **tabla dorada** (los resultados esperados que entregó el cliente para el buzón de muestra, más la tabla completa decidida para el resto) y un **set ciego** de 60 correos escritos por alguien que nunca vio el código. La tabla dorada demuestra que las reglas hacen lo que Martha describió; el set ciego estima cómo se comportan con correos para los que no se escribieron. Un documento que debe mirar una persona se reporta como "enviado a una persona", no se esconde entre los errores.

## Quién lo usa

- **Desarrolladores y el revisor**: corren la evaluación antes y después de cambiar una regla; las pruebas doradas deben seguir en 100 % y la línea base ciega no puede empeorar.
- **Coordinadora (COORDINATOR, Dra. Herrera) y la gerencia de TAC**: leen los resultados en el [resumen ejecutivo](../deliverables/00-resumen-ejecutivo.md) y en este documento para decidir cuánto confiar en las propuestas.
- **Auxiliar de radicación (CLERK, Martha)**: de forma indirecta; sus correcciones en producción son la siguiente medida (`docket_documents_approved_total{corrected=…}`, ver [observabilidad](observability.md)).
- **Asistente de IA vía MCP**: sin acceso.

## Cómo funciona

1. `app/evaluate.py` arma un contenedor nuevo sobre un directorio de datos temporal (procesador apagado), importa todos los `.eml` del set elegido con el actor `EVALUATION` y compara la decisión de cada documento con la fila esperada en cuatro campos: `document_type`, `department`, `action`, `due_date`.
2. Cada documento recibe un resultado: `CORRECT` (los cuatro campos coinciden), `ROUTED_TO_PERSON` (algo difiere pero el sistema lo marcó para revisión humana, así que nada se radica sin una persona), `WRONG` (algo difiere y el sistema estaba seguro) o `MISSING` (no se encontró el documento; cuenta como error).
3. El informe da totales por referencia, coincidencias por campo y, para cada documento que no acertó, sus códigos de razón; `--json` lo guarda.

```bash
cd api
uv run python -m app.evaluate --data-dir /tmp/docket-eval --set golden --ai off       # dorado: los 8 del cliente + tabla completa de 17
uv run python -m app.evaluate --data-dir /tmp/docket-blind --set blind --ai off       # set ciego: 65 documentos
uv run python -m app.evaluate --data-dir /tmp/docket-cmp --set blind --ai compare     # solo reglas frente a reglas + IA, lado a lado
```

### Tabla dorada (buzón de muestra, 16 correos, 17 documentos)

| Referencia | Fuente | Resultado |
|---|---|---|
| `client_partial` | `material/4-para-medirte/esperado-parcial.csv` (vocabulario del cliente) | **8/8** correctos |
| `full_table` | `api/tests/golden/esperado-completo.csv` | **17/17** con Tesseract; 16/17 + 1 enviado a una persona sin él (el escaneado `03.eml` queda como `DOCUMENT_UNREADABLE`) |

### Set ciego (`api/tests/blind/`)

- **60 correos con 65 documentos** (`emails/b01.eml` … `b60.eml`) y el resultado esperado en `esperado-ciego.csv`, generados por `generar.py`. Los escribió un agente que solo tuvo la entrevista, el maestro de proveedores, las dependencias y el libro: nunca leyó el código, la documentación ni las reglas. Todos los datos son ficticios (dominios `.example`).
- Formatos: 31 PDF nativos, 7 PDF escaneados (con ruido, rotación y desenfoque), 5 `.docx`, 22 cuerpos de correo (texto plano, solo HTML y multiparte), 5 correos con dos adjuntos; recibidos en fin de semana, en festivo y fuera de horario.
- `README.md` deja constancia de **26 decisiones de criterio** en las que la entrevista no dice nada o es ambigua (p. ej. un proveedor inactivo con orden de compra va a Compras; otro buzón del mismo dominio no es fraude).

**Resultado (con Tesseract): 45/65 correctos, 14 enviados a una persona, 6 errores.**

| Error | Casos | Por qué |
|---|---|---|
| Solicitudes de viáticos válidas devueltas al remitente | 4 | No se reconoce la aprobación en formatos con una disposición distinta a la de la muestra, así que la solicitud parece sin aprobar |
| Factura escaneada enviada a Compras en lugar de Cuentas por pagar | 1 | El OCR no leyó el número de la orden de compra, así que se aplicó la regla de "sin OC" |
| Consulta tomada como queja | 1 | Dependencia equivocada y 15 días en lugar de 30 |

Todos los casos que tocan plata se detectaron: **5/5 facturas retenidas por fraude** y **3/3 facturas duplicadas** quedaron retenidas o respondidas con el radicado existente; ninguna se radicó en silencio.

### Política: las reglas no se ajustaron al set ciego

El resultado ciego es una **medición, no una meta**. Las reglas no se cambiaron después de verlo; hacerlo volvería el set ciego otra tabla dorada y la cifra dejaría de significar algo. `tests/blind/test_blind_baseline.py` es un **piso**: falla si un cambio empeora a Docket con correos a los que nunca se ajustó (menos de 45 correctos, más de 6 errores, o cualquier caso de plata equivocado en silencio). Subir el piso exige un set ciego **nuevo**, escrito de la misma forma.

### Solo reglas frente a reglas + IA (medido el 2026-11-24, `claude-haiku-5-5`)

`--ai compare` corre el mismo buzón dos veces. La IA solo se consulta cuando las reglas encuentran ambiguo el tipo, y su respuesta es solo un tipo sugerido: dependencia, vencimiento, consecutivo, duplicados y fraude siguen en las reglas, y el documento igual va a revisión humana (`AMBIGUOUS_CLASSIFICATION` + `CLASSIFIED_BY_ASSISTANT`).

| Conjunto | Llamadas a la IA | Correctos | A una persona | Errores |
|---|---|---|---|---|
| Dorado (17) | 0 | 17 → 17 | 0 → 0 | 0 → 0 |
| Ciego (65) | 12 | 45 → 56 | 14 → 3 | 6 → 6 |

- Dorado: las reglas están seguras en todos los documentos, así que la IA nunca se consulta.
- Ciego: 11 documentos que llegaban sin propuesta útil ahora llegan con la correcta (b10, b13, b15, b18, b19, b26, b28, b41, b49, b54, b57). Igual necesitan la confirmación de Martha: los documentos en revisión siguen siendo 21/65.
- Los 6 errores no cambian: son casos en que las reglas están seguras y se equivocan, así que la IA nunca se consulta. Corregirlos es trabajo de reglas, no de IA.

## Reglas de negocio

| Regla | Fuente | Dónde está en el código |
|---|---|---|
| Ante la duda, preguntar en vez de inventar: un documento dudoso cuenta como enviado a una persona, no como correcto | Martha: *"que cuando no esté seguro me pregunte, en vez de inventarse algo"* | `evaluate` (`ROUTED_TO_PERSON` solo si `needs_review`) |
| El fraude y los duplicados nunca se equivocan en silencio | Reglas de fraude y duplicados de Martha; costo de un doble pago | `test_no_fraud_hold_or_duplicate_is_ever_missed` (`HOLD_FOR_VERIFICATION`, `REPLY_WITH_EXISTING_NUMBER`) |
| Los resultados esperados del cliente se mantienen en 100 % | Regla del proyecto ("La prueba dorada debe seguir en 100 %") | `api/tests/golden/test_golden.py`, `test_evaluate.py` |
| El set ciego no se usa para ajustar reglas | Validez de la medición | docstring de `test_blind_baseline.py`; `tests/blind/README.md` |

## Endpoints / pantallas

No hay endpoint ni pantalla. Puntos de entrada:

| Comando / archivo | Qué hace |
|---|---|
| `uv run python -m app.evaluate --data-dir <dir> --set golden\|blind --ai off\|on\|compare [--json out.json]` | Corre la evaluación e imprime el resumen y cada documento que no acertó. Ambas opciones son obligatorias (sin valores por defecto). `--ai on` necesita `TAC_LLM_ENABLED`, `TAC_ANTHROPIC_API_KEY` y `TAC_LLM_MODEL`; `--ai compare` corre ambas sobre el mismo buzón (`<dir>/without-ai`, `<dir>/with-ai`) y lista cada documento cuyo resultado cambió. El reporte cuenta las llamadas a la IA y las respuestas utilizables; nunca guarda el texto enviado. |
| `api/tests/golden/test_golden.py` | Una prueba por fila de la tabla del cliente y de la tabla completa |
| `api/tests/golden/test_evaluate.py` | El informe de evaluación coincide con las pruebas doradas (8/8; 17/17 o 16/17 sin OCR) |
| `api/tests/blind/test_blind_baseline.py` | Piso ciego (se omite sin Tesseract: el set tiene 7 escaneados) |

## Códigos

| Código | Meaning (EN) | Significado (ES) | ¿Bloquea? |
|---|---|---|---|
| `CORRECT` | Type, department, action and due date all match | Tipo, dependencia, acción y vencimiento coinciden | — |
| `ROUTED_TO_PERSON` | Differs, but the system sent it to human review | Difiere, pero el sistema lo mandó a revisión humana | — |
| `WRONG` | Differs and the system was confident | Difiere y el sistema estaba seguro | Hace fallar la línea base por encima de 6 |
| `MISSING` | Expected document not found (counted as wrong) | No se encontró el documento esperado (cuenta como error) | Hace fallar la línea base |

## Limitaciones

- El set ciego es **sintético**: está escrito para parecerse al correo de TAC, no es correo real. El acierto real es la tasa de corrección en producción.
- Los 6 errores del set ciego se conocen y todavía no se corrigen (aprobación en otros formatos de viáticos, OCR del número de OC en escaneados, consulta frente a queja); corregirlos debe validarse con un set ciego nuevo.
- La línea base ciega necesita Tesseract; en una máquina sin él la prueba se omite.
- En el set ciego no se evalúan los radicados (la columna `radicado` está vacía); los cubre la prueba dorada.
- Las respuestas esperadas del set ciego las escribió un solo anotador; sus 26 decisiones de criterio no las ha confirmado Martha.

## Cómo se prueba

- `api/tests/golden/test_golden.py`: `test_matches_the_clients_expected_results`, `test_matches_the_full_expected_table`, `test_filing_numbers_continue_the_ledger`.
- `api/tests/golden/test_evaluate.py::test_evaluation_report`.
- `api/tests/blind/test_blind_baseline.py`: `test_blind_baseline_does_not_regress` (65 documentos, ≥ 45 correctos, ≤ 6 errores) y `test_no_fraud_hold_or_duplicate_is_ever_missed`.

```bash
./scripts/harness-verify.sh api/tests/golden/test_golden.py api/tests/golden/test_evaluate.py
./scripts/harness-verify.sh api/tests/blind/test_blind_baseline.py
```

## Historial de cambios

- 2026-11-24: primera versión: tabla dorada (8/8, 17/17 con OCR), set ciego de 60 correos / 65 documentos (45 correctos, 14 enviados a una persona, 6 errores; todas las retenciones por fraude y los duplicados detectados), política de no ajustar y piso de la línea base.
- 2026-11-24: `--set` y `--ai off|on|compare` son obligatorios (sin valores por defecto); `--ai compare` mide solo reglas frente a reglas + IA (ciego: 45→56 correctos, 14→3 a una persona, 6→6 errores; 12 llamadas a la IA; dorado: 0 llamadas). El reporte cuenta las llamadas pero nunca guarda el texto enviado.
