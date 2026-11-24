"""Retention endpoints (Ley 594 de 2000)."""

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from app.features.records.application.use_cases import (
    DispositionNotAllowedError,
    RecordNotFoundError,
    RetentionNotExpiredError,
)
from app.features.records.domain.retention import RetentionStatus
from app.shared.domain.pagination import DEFAULT_LIMIT, PageRequest
from app.shared.infrastructure.http import (
    AnyRole,
    ApiError,
    ContainerDep,
    CoordinatorRole,
    Envelope,
    ok,
)

router = APIRouter(prefix="/api/retention", tags=["records"])


class DisposeRequest(BaseModel):
    record_reference: (
        str  # the disposal record approved by the archive committee (acta de eliminación)
    )


@router.get("/schedule")
def schedule(container: ContainerDep, _: AnyRole) -> Envelope:
    rules = container.get_retention_schedule()
    return ok(
        "RETENTION_SCHEDULE",
        [r.model_dump(mode="json") | {"total_years": r.total_years} for r in rules],
    )


@router.get("")
def list_retention(
    container: ContainerDep,
    _: AnyRole,
    status: RetentionStatus | None = None,
    on: date | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Envelope:
    """`on` lets the coordinator preview what will be due at a future date."""
    page = container.list_retention(
        on or container.settings.current_date(), status, PageRequest(limit=limit, offset=offset)
    )
    return ok("RETENTION_LISTED", page.model_dump(mode="json"))


@router.post("/{filing_number}/dispose")
def dispose(
    filing_number: str, body: DisposeRequest, container: ContainerDep, role: CoordinatorRole
) -> Envelope:
    if len(body.record_reference.strip()) < 3:
        raise ApiError(422, "DISPOSAL_RECORD_REQUIRED")
    try:
        view = container.dispose_record(
            filing_number, body.record_reference, container.settings.current_date(), role
        )
    except RecordNotFoundError as exc:
        raise ApiError(404, "RECORD_NOT_FOUND", filing_number=filing_number) from exc
    except RetentionNotExpiredError as exc:
        raise ApiError(409, "RETENTION_NOT_EXPIRED", filing_number=filing_number) from exc
    except DispositionNotAllowedError as exc:
        raise ApiError(409, "DISPOSITION_NOT_ALLOWED", filing_number=filing_number) from exc
    return ok("RECORD_DISPOSED", view.model_dump(mode="json"))
