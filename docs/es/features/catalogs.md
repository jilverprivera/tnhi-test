# Catálogos

## Propósito

Les da a las reglas de radicación los datos maestros del cliente: el **maestro de proveedores** (que Compras exporta del ERP) y las **dependencias** con sus correos. El maestro de proveedores es lo que hace posibles las reglas de facturas y antifraude: si el proveedor está creado o no, si está activo, y cuáles son la cuenta bancaria y el dominio de correo de facturación que se sabe que son legítimos.

## Quién lo usa

- **Auxiliar de radicación (CLERK, Martha)**: consulta proveedores y dependencias; carga una nueva exportación del maestro cuando Compras la envía (solo CLERK puede reemplazarlo).
- **Coordinadora (COORDINATOR, Dra. Herrera)**: los consulta.
- **Asistente de IA vía MCP**: no tiene herramientas de catálogos.
- **Módulo de radicación**: `supplier_master().by_nit()` / `by_domain()` y `departments()` (direcciones de la bandeja de salida).

## Cómo funciona

1. **Maestro de proveedores**: la primera vez que se usa, el contenedor copia `TAC_SUPPLIERS_CSV` (`material/3-datos-del-cliente/maestro-proveedores.csv`) a `TAC_DATA_DIR/maestro-proveedores.csv`; en `material/` nunca se escribe. `CsvCatalogs` lee la copia de trabajo una vez y la mantiene en memoria.
2. Columnas obligatorias: `nit`, `razon_social`, `correo_facturacion`, `banco`, `tipo_cuenta`, `numero_cuenta`, `estado`, `categoria`. Un proveedor está activo cuando `estado` es `ACTIVO`.
3. Búsquedas: `by_nit` compara los NIT normalizados a dígitos (sin puntos ni guion); `by_domain` compara el dominio exacto del correo de facturación (así, uno parecido como `aseointegral-bogota.example` **no** coincide con `aseointegralbogota.example`).
4. **Reemplazo** (`PUT /api/catalogs/suppliers`): el CSV cargado se valida primero; si le faltan columnas se rechaza con `SUPPLIER_MASTER_INVALID` y se conserva el maestro anterior. Si es válido, sobrescribe la copia de trabajo y el maestro en memoria. Solo lo usan los documentos que se importen después.
5. **Dependencias**: se leen de `TAC_DEPARTMENTS_CSV` (`dependencias.csv`: `codigo`, `dependencia`, `correo`, `que_recibe`) en cada consulta, traduciendo los códigos del cliente (`CUENTAS_POR_PAGAR`, `COMPRAS`, `TALENTO_HUMANO`, `JURIDICA`, `ATENCION_USUARIO`) a códigos `Department`. Los códigos desconocidos se ignoran.

## Reglas de negocio

| Regla | Fuente | Dónde está en el código |
|---|---|---|
| El proveedor se busca en el maestro por NIT | Martha: *"Compras saca del sistema la lista de proveedores, el maestro, y yo lo busco ahí por el NIT."* | `SupplierMaster.by_nit` |
| La cuenta y el correo del maestro son los confiables (control antifraude) | Martha: *"si la cuenta de la factura no es la que está en el maestro, o el correo llega de una dirección rara…"* | `Supplier.account_number`, `Supplier.domain` |
| Cada dependencia recibe documentos específicos en su propio correo | `dependencias.csv` ("que_recibe") | `CsvCatalogs.departments` |
| Los datos del cliente son de solo lectura | Regla del proyecto: en `material/` nunca se escribe | copia de trabajo en `TAC_DATA_DIR` |

## Endpoints / pantallas

| Método | Ruta | Rol | Solicitud | `code` de éxito | Errores |
|---|---|---|---|---|---|
| GET | `/api/catalogs/suppliers` | cualquiera | — | `SUPPLIERS_LISTED` (`nit`, `name`, `billing_email`, `bank`, `account_type`, `account_number`, `status`, `category`, `is_active`) | `401` |
| PUT | `/api/catalogs/suppliers` | CLERK | multipart, campo `file` (CSV, UTF-8) | `SUPPLIER_MASTER_REPLACED` (`{"suppliers": n}`) | `422 SUPPLIER_MASTER_INVALID` (`detail.missing_columns`), `403 FORBIDDEN` |
| GET | `/api/catalogs/departments` | cualquiera | — | `DEPARTMENTS_LISTED` (`code`, `client_code`, `name`, `email`, `receives`) | `401` |

## Códigos

| Código | Meaning (EN) | Significado (ES) | ¿Bloquea? |
|---|---|---|---|
| `SUPPLIERS_LISTED` | Supplier master returned | Maestro de proveedores devuelto | — |
| `SUPPLIER_MASTER_REPLACED` | New supplier master loaded | Se cargó el nuevo maestro de proveedores | — |
| `SUPPLIER_MASTER_INVALID` | Uploaded CSV lacks required columns; old master kept | Al CSV cargado le faltan columnas; se conserva el maestro anterior | — (HTTP 422) |
| `DEPARTMENTS_LISTED` | Departments returned | Dependencias devueltas | — |

## Limitaciones

- Reemplazar el maestro de proveedores **todavía no** deja evento de auditoría (la regla del proyecto lo exige para toda modificación).
- El maestro es una exportación CSV; leer el ERP directamente sería otro adaptador de `CatalogSource`.
- Las propuestas que ya están en la bandeja no se recalculan cuando se reemplaza el maestro.
- Las filas no se validan una por una (p. ej. dígito de verificación del NIT, cuenta vacía).
- `ADMIN_COORDINATION` no está en `dependencias.csv`; las alertas de fraude usan una dirección fija de la coordinación definida en el módulo de radicación.

## Cómo se prueba

- `api/tests/features/catalogs/test_catalogs.py`: búsqueda por NIT y por dominio (dominio parecido rechazado, proveedor inactivo), códigos y correos de las dependencias del cliente, una carga inválida se rechaza y se conserva el maestro anterior (10 proveedores).
- De forma indirecta, `api/tests/features/filing/test_rules.py` y las pruebas golden.

```bash
./scripts/harness-verify.sh api/tests/features/catalogs/test_catalogs.py
```
