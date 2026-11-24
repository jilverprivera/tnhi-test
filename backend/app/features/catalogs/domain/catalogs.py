"""Master data: suppliers (exported from the ERP by Procurement) and departments."""

from dataclasses import dataclass

from app.shared.domain.identifiers import email_domain, normalize_nit
from app.shared.domain.models import Department


@dataclass(frozen=True)
class Supplier:
    nit: str
    name: str
    billing_email: str
    bank: str
    account_type: str
    account_number: str
    status: str
    category: str

    @property
    def is_active(self) -> bool:
        return self.status.strip().upper() == "ACTIVO"

    @property
    def domain(self) -> str:
        return email_domain(self.billing_email)


@dataclass(frozen=True)
class DepartmentInfo:
    code: Department
    client_code: str
    name: str
    email: str
    receives: str


class SupplierMaster:
    """In-memory lookup over the supplier master."""

    def __init__(self, suppliers: list[Supplier]):
        self.suppliers = suppliers
        self._by_nit = {normalize_nit(s.nit): s for s in suppliers}

    def by_nit(self, nit: str) -> Supplier | None:
        return self._by_nit.get(normalize_nit(nit))

    def by_domain(self, address: str) -> Supplier | None:
        domain = email_domain(address)
        return next((s for s in self.suppliers if s.domain == domain), None)
