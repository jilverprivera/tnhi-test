import pytest

from app.features.catalogs.infrastructure.csv_catalogs import InvalidSupplierMasterError
from app.shared.domain.models import Department


def test_master_lookup_by_nit_and_domain(container):
    master = container.catalogs.supplier_master()
    assert master.by_nit("901112233-4").name == "Aseo Integral Bogotá S.A.S."
    assert master.by_domain("x@aseointegralbogota.example") is not None
    assert master.by_domain("x@aseointegral-bogota.example") is None  # look-alike domain
    assert not master.by_nit("800.777.666-1").is_active


def test_departments_map_client_codes(container):
    departments = container.catalogs.departments()
    assert departments[Department.ACCOUNTS_PAYABLE].client_code == "CUENTAS_POR_PAGAR"
    assert departments[Department.LEGAL].email == "juridica@terminalesandinas.example"


def test_invalid_master_upload_is_rejected_and_keeps_the_old_one(container):
    with pytest.raises(InvalidSupplierMasterError):
        container.catalogs.replace_supplier_master(b"nit,razon_social\n1,x\n")
    assert len(container.catalogs.supplier_master().suppliers) == 10
