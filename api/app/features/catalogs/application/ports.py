"""Catalog ports: today they are exported CSV files; tomorrow, the ERP itself."""

from typing import Protocol

from app.features.catalogs.domain.catalogs import DepartmentInfo, SupplierMaster
from app.shared.domain.models import Department


class CatalogSource(Protocol):
    def supplier_master(self) -> SupplierMaster: ...

    def departments(self) -> dict[Department, DepartmentInfo]: ...

    def replace_supplier_master(self, csv_content: bytes) -> SupplierMaster: ...
