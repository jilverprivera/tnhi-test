"""Catalog endpoints: supplier master and departments."""

from dataclasses import asdict

from fastapi import APIRouter, UploadFile

from app.features.catalogs.infrastructure.csv_catalogs import InvalidSupplierMasterError
from app.shared.infrastructure.http import AnyRole, ApiError, ClerkRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.get("/suppliers")
def list_suppliers(container: ContainerDep, _: AnyRole) -> Envelope:
    master = container.catalogs.supplier_master()
    return ok(
        "SUPPLIERS_LISTED", [asdict(s) | {"is_active": s.is_active} for s in master.suppliers]
    )


@router.put("/suppliers")
async def replace_suppliers(file: UploadFile, container: ContainerDep, _: ClerkRole) -> Envelope:
    try:
        master = container.catalogs.replace_supplier_master(await file.read())
    except InvalidSupplierMasterError as exc:
        raise ApiError(422, "SUPPLIER_MASTER_INVALID", missing_columns=str(exc)) from exc
    return ok("SUPPLIER_MASTER_REPLACED", {"suppliers": len(master.suppliers)})


@router.get("/departments")
def list_departments(container: ContainerDep, _: AnyRole) -> Envelope:
    return ok("DEPARTMENTS_LISTED", [asdict(d) for d in container.catalogs.departments().values()])
