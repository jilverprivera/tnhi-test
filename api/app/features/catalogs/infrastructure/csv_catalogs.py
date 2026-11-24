"""Adapter: catalogs read from the CSV files exported by the client's ERP."""

import csv
import io
from pathlib import Path

from app.features.catalogs.domain.catalogs import DepartmentInfo, Supplier, SupplierMaster
from app.shared.domain.models import Department
from app.shared.infrastructure.client_vocabulary import CLIENT_CODE_TO_DEPARTMENT

# Client CSV column -> Supplier attribute
SUPPLIER_COLUMNS = {
    "nit": "nit",
    "razon_social": "name",
    "correo_facturacion": "billing_email",
    "banco": "bank",
    "tipo_cuenta": "account_type",
    "numero_cuenta": "account_number",
    "estado": "status",
    "categoria": "category",
}


class InvalidSupplierMasterError(ValueError):
    pass


def parse_supplier_master(text: str) -> SupplierMaster:
    reader = csv.DictReader(io.StringIO(text))
    missing = set(SUPPLIER_COLUMNS) - set(reader.fieldnames or [])
    if missing:
        raise InvalidSupplierMasterError(",".join(sorted(missing)))
    return SupplierMaster(
        [
            Supplier(**{attr: row[col].strip() for col, attr in SUPPLIER_COLUMNS.items()})
            for row in reader
        ]
    )


class CsvCatalogs:
    def __init__(self, suppliers_csv: Path, departments_csv: Path):
        self._suppliers_csv = suppliers_csv
        self._departments_csv = departments_csv
        self._master: SupplierMaster | None = None

    def supplier_master(self) -> SupplierMaster:
        if self._master is None:
            self._master = parse_supplier_master(
                self._suppliers_csv.read_text(encoding="utf-8-sig")
            )
        return self._master

    def departments(self) -> dict[Department, DepartmentInfo]:
        with open(self._departments_csv, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        return {
            CLIENT_CODE_TO_DEPARTMENT[r["codigo"]]: DepartmentInfo(
                code=CLIENT_CODE_TO_DEPARTMENT[r["codigo"]],
                client_code=r["codigo"],
                name=r["dependencia"],
                email=r["correo"],
                receives=r["que_recibe"],
            )
            for r in rows
            if r["codigo"] in CLIENT_CODE_TO_DEPARTMENT
        }

    def replace_supplier_master(self, csv_content: bytes) -> SupplierMaster:
        text = csv_content.decode("utf-8-sig")
        master = parse_supplier_master(text)  # validate before overwriting
        self._suppliers_csv.write_text(text, encoding="utf-8")
        self._master = master
        return master
