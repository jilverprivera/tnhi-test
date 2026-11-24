# Catalogs

## Purpose

Gives the filing rules the client's master data: the **supplier master** (exported from the ERP by Procurement) and the **departments** with their e-mail addresses. The supplier master is what makes the invoice and anti-fraud rules possible: registered or not, active or not, the bank account and billing e-mail domain that are known to be legitimate.

## Who uses it

- **Clerk (CLERK, Martha)**: consults suppliers and departments; uploads a new export of the supplier master when Procurement sends one (only CLERK can replace it).
- **Coordinator (COORDINATOR, Dra. Herrera)**: consults them.
- **AI assistant via MCP**: no catalog tools.
- **Filing slice**: `supplier_master().by_nit()` / `by_domain()` and `departments()` (outbox addresses).

## How it works

1. **Supplier master**: on first use the container copies `TAC_SUPPLIERS_CSV` (`material/3-datos-del-cliente/maestro-proveedores.csv`) to `TAC_DATA_DIR/maestro-proveedores.csv`; `material/` is never written. `CsvCatalogs` parses the working copy once and keeps it in memory.
2. Columns required: `nit`, `razon_social`, `correo_facturacion`, `banco`, `tipo_cuenta`, `numero_cuenta`, `estado`, `categoria`. A supplier is active when `estado` is `ACTIVO`.
3. Lookups: `by_nit` compares NITs normalized to digits (dots and dash removed); `by_domain` compares the exact domain of the billing e-mail (so a look-alike such as `aseointegral-bogota.example` does **not** match `aseointegralbogota.example`).
4. **Replace** (`PUT /api/catalogs/suppliers`): the uploaded CSV is validated first; if columns are missing it is rejected with `SUPPLIER_MASTER_INVALID` and the previous master stays in place. If valid, it overwrites the working copy and the in-memory master. Only documents imported afterwards use it.
5. **Departments**: read from `TAC_DEPARTMENTS_CSV` (`dependencias.csv`: `codigo`, `dependencia`, `correo`, `que_recibe`) on every call, mapping client codes (`CUENTAS_POR_PAGAR`, `COMPRAS`, `TALENTO_HUMANO`, `JURIDICA`, `ATENCION_USUARIO`) to `Department` codes. Unknown client codes are ignored.

## Business rules

| Rule | Source | Where in code |
|---|---|---|
| The supplier is looked up in the master by NIT | Martha: *"Compras saca del sistema la lista de proveedores, el maestro, y yo lo busco ahí por el NIT."* | `SupplierMaster.by_nit` |
| The account and e-mail in the master are the trusted ones (fraud guard) | Martha: *"si la cuenta de la factura no es la que está en el maestro, o el correo llega de una dirección rara…"* | `Supplier.account_number`, `Supplier.domain` |
| Each department receives specific documents at its own address | `dependencias.csv` ("que_recibe") | `CsvCatalogs.departments` |
| Client data is read-only | Guardrail: `material/` is never written | working copy in `TAC_DATA_DIR` |

## API endpoints / screens

| Method | Path | Role | Request | Success `code` | Errors |
|---|---|---|---|---|---|
| GET | `/api/catalogs/suppliers` | any | — | `SUPPLIERS_LISTED` (`nit`, `name`, `billing_email`, `bank`, `account_type`, `account_number`, `status`, `category`, `is_active`) | `401` |
| PUT | `/api/catalogs/suppliers` | CLERK | multipart field `file` (CSV, UTF-8) | `SUPPLIER_MASTER_REPLACED` (`{"suppliers": n}`) | `422 SUPPLIER_MASTER_INVALID` (`detail.missing_columns`), `403 FORBIDDEN` |
| GET | `/api/catalogs/departments` | any | — | `DEPARTMENTS_LISTED` (`code`, `client_code`, `name`, `email`, `receives`) | `401` |

## Codes

| Code | Meaning (EN) | Significado (ES) | Blocking? |
|---|---|---|---|
| `SUPPLIERS_LISTED` | Supplier master returned | Maestro de proveedores devuelto | — |
| `SUPPLIER_MASTER_REPLACED` | New supplier master loaded | Se cargó el nuevo maestro de proveedores | — |
| `SUPPLIER_MASTER_INVALID` | Uploaded CSV lacks required columns; old master kept | Al CSV cargado le faltan columnas; se conserva el maestro anterior | — (HTTP 422) |
| `DEPARTMENTS_LISTED` | Departments returned | Dependencias devueltas | — |

## Limitations

- Replacing the supplier master does **not** record an audit event yet (the guardrail requires one for every mutation).
- The master is a CSV export; reading the ERP directly would be another `CatalogSource` adapter.
- Proposals already in the inbox are not recalculated after the master is replaced.
- Rows are not validated individually (e.g. NIT check digit, empty account).
- `ADMIN_COORDINATION` is not in `dependencias.csv`; fraud alerts use a fixed coordinator address in the filing slice.

## How it is tested

- `api/tests/features/catalogs/test_catalogs.py`: lookup by NIT and by domain (look-alike domain rejected, inactive supplier), client department codes and e-mails, invalid upload rejected keeping the old master (10 suppliers).
- Indirectly by `api/tests/features/filing/test_rules.py` and the golden tests.

```bash
./scripts/harness-verify.sh api/tests/features/catalogs/test_catalogs.py
```
