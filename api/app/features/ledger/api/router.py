"""Ledger endpoints: query, Excel export and duplicate report."""

from fastapi import APIRouter
from fastapi.responses import Response

from app.features.ledger.application.use_cases import LedgerQuery
from app.shared.domain.pagination import DEFAULT_LIMIT, PageRequest
from app.shared.infrastructure.http import AnyRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/ledger", tags=["ledger"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("")
def list_ledger(
    container: ContainerDep,
    _: AnyRole,
    q: str = "",
    department: str = "",
    document_type: str = "",
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Envelope:
    query = LedgerQuery(text=q, department=department, document_type=document_type)
    page = container.paginate_ledger(query, PageRequest(limit=limit, offset=offset))
    return ok("LEDGER_LISTED", page.model_dump(mode="json"))


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


@router.get("/sync")
def sync_status(container: ContainerDep, _: AnyRole) -> Envelope:
    state = container.sync_ledger.last_state()
    return ok("LEDGER_SYNC_STATUS", state.model_dump(mode="json") if state else None)


@router.post("/sync")
def sync_now(container: ContainerDep, role: AnyRole) -> Envelope:
    """Merge now: imports rows typed by hand and edits made in the shared Excel."""
    state = container.sync_ledger(actor=role)
    return ok(f"LEDGER_{state.outcome}", state.model_dump(mode="json"))
