"""Ledger endpoints: query, Excel export and duplicate report."""

from fastapi import APIRouter
from fastapi.responses import Response

from app.features.ledger.application.use_cases import LedgerQuery
from app.shared.infrastructure.http import AnyRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/ledger", tags=["ledger"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("")
def list_ledger(
    container: ContainerDep, _: AnyRole, q: str = "", department: str = "", document_type: str = ""
) -> Envelope:
    entries = container.list_ledger(
        LedgerQuery(text=q, department=department, document_type=document_type)
    )
    return ok("LEDGER_LISTED", [e.model_dump(mode="json") for e in entries])


@router.get("/export")
def export_ledger(container: ContainerDep, _: AnyRole) -> Response:
    return Response(
        container.export_ledger(),
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="libro-radicacion-2026.xlsx"'},
    )


@router.get("/duplicates")
def ledger_duplicates(container: ContainerDep, _: AnyRole) -> Envelope:
    return ok("LEDGER_DUPLICATES", container.find_ledger_duplicates())
