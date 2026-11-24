# Set de evaluación ciego — radicación TAC

60 correos (`emails/b01.eml` … `b60.eml`) con 65 documentos, y su resultado esperado en
`esperado-ciego.csv`. Todo es ficticio (dominios `.example`).

## Cómo se construyó

- Las respuestas esperadas salen **solo** de: la entrevista con Martha
  (`material/1-entrevista/transcripcion-entrevista-martha.md`), el maestro de proveedores, `dependencias.csv`
  y el libro `libro-radicacion-2026.xlsx` (para duplicados). No se leyó el código del sistema
  (`api/app`, `web`, `docs`, `entregables`, `.claude`, `CLAUDE.md`) ni se ejecutó el sistema.
- `generar.py` contiene los 60 casos (contenido + resultado esperado) y genera todo:
  `cd api && uv run python tests/blind/generar.py`. Es determinista (semilla fija para el ruido de los escaneos;
  los Message-ID sí cambian en cada ejecución).
- Los correos se arman con `email.message.EmailMessage` (From, To, Date, Subject, Message-ID). Se ordenan
  por fecha de recepción y se numeran en ese orden.
- Los vencimientos los calcula el script (`add_business` / `add_calendar`), no se escribieron a mano.
- Columna `radicado`: vacía siempre (la numeración no se evalúa en este set). Para los duplicados, el
  radicado existente se cita en `observacion`.

### Formatos

| Formato | Cantidad | Detalle |
|---|---|---|
| PDF con texto | 31 | Generador PDF mínimo propio en `generar.py` (`text_pdf`): una página, Helvetica/Helvetica-Bold Type1, WinAnsiEncoding (tildes y ñ extraíbles; comprobado con pdfplumber) |
| PDF escaneado (solo imagen) | 7 | `scanned_pdf`: texto dibujado con Pillow (Courier New), ruido, ligera rotación y desenfoque, guardado como PDF de imagen sin capa de texto (b05, b11, b15, b20, b31, b36, b50) |
| .docx | 5 | python-docx (b18, b34, b41, b42, b59) |
| Cuerpo del correo | 22 | texto plano, HTML solo (b19, b28, b43, b46) o multipart/alternative texto+HTML (b04, b26, b35) |
| Correos con 2 adjuntos | 5 | b17, b36, b37, b39, b43 |

## Convenciones aplicadas

- "Hoy" = 2026-11-18. Recepción entre el 3 y el 17 de nov de 2026, `-0500`, con correos en sábado,
  domingo, festivo (16 nov) y fuera de horario.
- Días no hábiles: sábados, domingos y festivos 2026-11-02, 2026-11-16, 2026-12-08, 2026-12-25, y para
  plazos largos 2027-01-01 y 2027-01-11 (ninguno de los vencimientos del set llega a 2027).
- Términos en días hábiles: el día 1 es el día hábil siguiente a la fecha de recepción. Coincide con la
  fila de `esperado-parcial.csv` (10.eml: recibido 10 nov → 15 días → 2 dic).
- Prioridad para facturas: **fraude (retener) > duplicado (responder) > no registrado / inactivo (Compras)
  > con OC (Cuentas por pagar) / sin OC (Compras)**. En el set no hay casos que combinen fraude con
  duplicado, así que la prioridad entre esas dos no se está midiendo.

## Distribución

Por tipo (documentos):

| tipo | docs |
|---|---|
| INVOICE | 25 |
| PETITION | 10 |
| TRAVEL_EXPENSE_REQUEST | 9 |
| COMPLAINT | 7 |
| OVERSIGHT_NOTICE | 5 |
| ADVERTISING | 5 |
| QUOTATION | 4 |
| **Total** | **65** |

Por dependencia / acción:

| dependencia | accion | docs |
|---|---|---|
| LEGAL | FILE | 15 |
| PROCUREMENT | FILE | 12 (8 facturas, 4 cotizaciones) |
| ACCOUNTS_PAYABLE | FILE | 9 |
| CUSTOMER_SERVICE | FILE | 7 |
| SENDER | RETURN_TO_SENDER | 5 |
| ADMIN_COORDINATION | HOLD_FOR_VERIFICATION | 5 |
| NONE | DO_NOT_FILE | 5 |
| HUMAN_RESOURCES | FILE | 4 (1 extemporánea) |
| SENDER | REPLY_WITH_EXISTING_NUMBER | 3 |

Facturas (25): 9 Cuentas por pagar · 8 Compras (4 sin OC, 3 no registrados, 1 proveedor INACTIVO) ·
5 retenidas por fraude · 3 duplicadas.

## Casos de prueba destacados

- **Duplicados reales** (mismo proveedor + mismo número en el libro): b05 SE-77790 Sabana
  (TAC-2026-ER-04791, asunto "COBRO PENDIENTE", escaneado), b09 AIB-2026-1102 Aseo (RV:, ER-04795),
  b36 FV-10498 Ferretería (ER-04794, desde otro buzón del mismo dominio, junto con una factura nueva).
- **Número repetido de otro proveedor (NO duplicado)**: b12 FE-1207 de Software Contable Nube; en el libro
  FE-1207 es de Papelería Colombia.
- **Fraude**: b27 cuenta distinta en la factura (mismo dominio); b29 dominio parecido
  `suministros-llano.example` con cuenta correcta; b38 dominio `sabanaexpres.example` + cuenta nueva;
  b16 correo personal `gmail.example`; b60 cuenta distinta solo en el cuerpo del correo.
- **Implícitos/trampas**: peticiones sin la frase "derecho de petición" (b35, b44, b53), queja que también
  pregunta (b22), publicidad que menciona "factura" (b33) o "derecho de petición/tutela" (b49), cuenta de
  cobro de persona natural (b41), NIT sin puntos (b56), asunto en mayúsculas sin tildes (b21, b56),
  reenvíos RV:/FW: (b09, b30, b57, b59).

## Decisiones de criterio (la entrevista no lo dice o es ambigua)

1. **Proveedor INACTIVO** (Vigilancia Técnica Andina, b25): aunque trae OC, se espera
   `PROCUREMENT / FILE`. Razón: Martha manda a pago solo a proveedores "creados"; uno inactivo no se puede
   pagar y es Compras quien vincula/reactiva proveedores. No se trata como fraude (cuenta y dominio coinciden).
2. **Proveedor no registrado con OC** (b45): `PROCUREMENT`. La regla de registro se aplica antes que la de OC.
3. **Proveedor no registrado**: no se aplica la verificación de cuenta/dominio (no hay contra qué comparar).
4. **"Dirección rara"** = el dominio del remitente no es el dominio del `correo_facturacion` del maestro.
   Otro buzón del **mismo** dominio (b36 `cartera@ferrela13.example` frente a `ventas@`) **no** es fraude
   ("a veces desde otro correo").
5. **Factura sin datos bancarios** (b60 PDF sin cuenta): la ausencia de cuenta no es discrepancia; en b60 la
   retención se debe a la cuenta distinta que pide el **correo**. La regla se aplica a cuenta en la factura
   o en el correo.
6. **OC solo en el cuerpo del correo** (b20, b17 LS-20931): cuenta como "trae OC".
7. **Cuenta de cobro / propuesta económica**: cuenta de cobro = INVOICE; "propuesta económica" y oferta en
   el cuerpo = QUOTATION. Las reglas de fraude no se aplican a cotizaciones.
8. **Correo con factura + cotización** (b39): cada adjunto es un documento con su propia ruta.
9. **Viáticos aprobados por correo pero sin firma en el formato** (b30): `RETURN_TO_SENDER`. Martha pide
   "el formato TH-F-012 con la firma del jefe"; la aprobación por correo no reemplaza la firma.
10. **Viáticos en un formato distinto, aunque firmado** (b10): `RETURN_TO_SENDER` (debe ser TH-F-012).
11. **Viáticos sin firma y además tardíos** (b48): se devuelve (la falta de firma prevalece).
12. **Anticipación de 5 días hábiles**: se cuentan los días hábiles entre la recepción y la salida. Los
    casos se eligieron lejos del umbral (b42: 1 día hábil → extemporánea; los demás ≥ 10) para que la
    forma exacta de contar no cambie el resultado. Los viáticos no llevan `vence`.
13. **Correo con dos formatos de viáticos** (b37): uno firmado (radicar) y otro sin firma (devolver), cada
    uno es un documento.
14. **Queja de un no usuario del terminal** (b44, vecina por tractomulas en la calle): es PETITION → LEGAL,
    15 días ("si no es una queja de un usuario del terminal, eso también es una petición").
15. **Cliente del terminal que pide un concepto** (b24): PETITION de consulta, 30 días; no es queja.
16. **Petición que anuncia tutela** (b40): LEGAL/FILE con el plazo normal (15) y "URGENTE" en observación.
    El set no tiene columna de urgencia; la urgencia solo va en la observación.
17. **Hora de recepción**: la fecha de recepción es la fecha calendario del encabezado Date, sin importar la
    hora. Para no depender de esta regla, ninguna petición, oficio ni queja con plazo llega fuera de horario
    en día hábil; los que llegan en fin de semana (b21 domingo, b53 domingo) dan el mismo resultado con
    cualquier criterio razonable.
18. **Reenvíos internos** (b57, b59): el plazo se cuenta desde la llegada al buzón de radicación; en ambos el
    original es del mismo día, así que no cambia nada.
19. **Oficios con plazo en palabras**: "diez (10) días hábiles" (b07), "cinco (5) días hábiles" (b31).
    **Días calendario** (b14 Personería, 8 días calendario): se cuentan desde el día siguiente a la recepción
    (5 nov + 8 = 13 nov, que cae en día hábil, así que no hay que correr la fecha).
20. **Juzgados**: un plazo en "días" sin decir "hábiles" (b58 tutela, "dos (2) días") se cuenta en días
    hábiles (los términos judiciales en días son hábiles). b47 dice explícitamente "tres (3) días hábiles".
21. **Tutela notificada por juzgado** (b58): OVERSIGHT_NOTICE (juzgado), LEGAL, plazo del auto.
22. **Copias + otras cosas** (b32): 15 días (regla de la abogada). Solo copias (b13, b15): 10.
23. **Publicidad de un proveedor registrado** (b19): sigue siendo ADVERTISING / NONE / DO_NOT_FILE.
24. **Factura recibida en festivo** (b55): no cambia la ruta; las facturas no llevan `vence`.
25. **Fechas de los correos frente al libro**: el libro tiene registros hasta el 9 nov y no contiene ninguno
    de los documentos nuevos del set. Se asume que el set se procesa contra el libro tal como está (solo
    sirve para detectar duplicados).
26. **Formato del CSV**: se usan los códigos en inglés pedidos (no los de `esperado-parcial.csv`), y
    `EMAIL_BODY` cuando el documento es el cuerpo del correo.
