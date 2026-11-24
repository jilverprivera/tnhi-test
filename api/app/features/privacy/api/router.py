"""Habeas data endpoints (Ley 1581 de 2012)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.features.privacy.application.subject_requests import IdentifierTooShortError, RequestKind
from app.features.privacy.domain.inventory import INVENTORY, SAFEGUARDS
from app.shared.infrastructure.http import (
    AnyRole,
    ApiError,
    ContainerDep,
    CoordinatorRole,
    Envelope,
    ok,
)

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


class SubjectRequest(BaseModel):
    identifier: (
        str  # national ID or e-mail; sent in the body so it never lands in URLs or access logs
    )
    kind: RequestKind = RequestKind.INQUIRY


@router.get("/inventory")
def inventory(_: AnyRole) -> Envelope:
    return ok(
        "PRIVACY_INVENTORY",
        {"items": [i.model_dump() for i in INVENTORY], "safeguards": SAFEGUARDS},
    )


@router.post("/subject-requests")
def subject_request(
    body: SubjectRequest, container: ContainerDep, role: CoordinatorRole
) -> Envelope:
    try:
        report = container.find_data_subject(
            body.identifier, body.kind, container.settings.current_date(), role
        )
    except IdentifierTooShortError as exc:
        raise ApiError(422, "IDENTIFIER_TOO_SHORT") from exc
    return ok("SUBJECT_REPORT", report.model_dump(mode="json"))
