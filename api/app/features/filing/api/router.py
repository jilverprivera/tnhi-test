"""Filing inbox endpoints (driving adapter)."""

from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.features.filing.api.views import inbox_item_view
from app.features.filing.application.approve_documents import (
    DecisionIncompleteError,
    DocumentNotApprovableError,
    DocumentNotFoundError,
    HoldRequiresEscalationError,
    NotAHoldError,
)
from app.features.filing.application.correct_document import (
    Correction,
    CorrectionIncompleteError,
    DocumentAlreadyClosedError,
)
from app.shared.domain.models import DocumentStatus
from app.shared.domain.pagination import DEFAULT_LIMIT, PageRequest
from app.shared.infrastructure.http import AnyRole, ApiError, ClerkRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/inbox", tags=["filing"])


class ApproveRequest(BaseModel):
    ids: list[str]


class DiscardRequest(BaseModel):
    reason: str


@router.get("")
def list_inbox(
    container: ContainerDep,
    _: AnyRole,
    status: Annotated[list[DocumentStatus] | None, Query()] = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> Envelope:
    page = container.paginate_inbox(status, PageRequest(limit=limit, offset=offset))
    items = [inbox_item_view(i) for i in page.items]
    return ok("INBOX_LISTED", page.model_dump(mode="json", exclude={"items"}) | {"items": items})


@router.get("/summary")
def inbox_summary(container: ContainerDep, _: AnyRole) -> Envelope:
    return ok("INBOX_SUMMARY", container.inbox_summary())


@router.post("/approve")
def approve(body: ApproveRequest, container: ContainerDep, role: ClerkRole) -> Envelope:
    try:
        approved = container.approve_documents(body.ids, actor=role)
    except DocumentNotFoundError as exc:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=str(exc)) from exc
    except DecisionIncompleteError as exc:
        raise ApiError(409, "DECISION_INCOMPLETE", id=str(exc)) from exc
    except HoldRequiresEscalationError as exc:
        raise ApiError(409, "HOLD_REQUIRES_ESCALATION", id=str(exc)) from exc
    return ok("DOCUMENTS_APPROVED", [inbox_item_view(i) for i in approved])


@router.post("/{document_id}/escalate")
def escalate(document_id: str, container: ContainerDep, role: ClerkRole) -> Envelope:
    """Suspected fraud: alert the coordinator (filed as ON_HOLD, never forwarded to payment)."""
    try:
        item = container.escalate_hold(document_id, actor=role)
    except DocumentNotFoundError as exc:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=document_id) from exc
    except NotAHoldError as exc:
        raise ApiError(409, "NOT_A_HOLD", id=document_id) from exc
    except DecisionIncompleteError as exc:
        raise ApiError(409, "DECISION_INCOMPLETE", id=document_id) from exc
    return ok("HOLD_ESCALATED", inbox_item_view(item))


@router.post("/approve-ready")
def approve_ready(container: ContainerDep, role: ClerkRole) -> Envelope:
    try:
        approved = container.approve_ready(actor=role)
    except DocumentNotApprovableError as exc:
        raise ApiError(409, "DOCUMENT_NEEDS_REVIEW", id=str(exc)) from exc
    except DecisionIncompleteError as exc:
        raise ApiError(409, "DECISION_INCOMPLETE", id=str(exc)) from exc
    return ok("DOCUMENTS_APPROVED", [inbox_item_view(i) for i in approved])


@router.get("/{document_id}")
def get_item(document_id: str, container: ContainerDep, _: AnyRole) -> Envelope:
    item = container.get_inbox_item(document_id)
    if item is None:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=document_id)
    view = inbox_item_view(item, include_text=True)
    view["audit"] = container.list_audit(document_id)
    return ok("DOCUMENT_FOUND", view)


@router.get("/{document_id}/source")
def get_source(document_id: str, container: ContainerDep, _: AnyRole) -> Response:
    source = container.inbox_repository.source_file(document_id)
    if source is None:
        raise ApiError(404, "SOURCE_FILE_NOT_FOUND", id=document_id)
    content, mime = source
    return Response(content, media_type=mime, headers={"Content-Disposition": "inline"})


@router.post("/{document_id}/correct")
def correct(
    document_id: str, body: Correction, container: ContainerDep, role: ClerkRole
) -> Envelope:
    try:
        item = container.correct_document(document_id, body, actor=role)
    except DocumentNotFoundError as exc:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=document_id) from exc
    except DocumentAlreadyClosedError as exc:
        raise ApiError(409, "DOCUMENT_ALREADY_CLOSED", id=document_id) from exc
    except CorrectionIncompleteError as exc:
        raise ApiError(422, "DECISION_INCOMPLETE", id=document_id) from exc
    return ok("DOCUMENT_CORRECTED", inbox_item_view(item, include_text=True))


@router.post("/{document_id}/discard")
def discard(
    document_id: str, body: DiscardRequest, container: ContainerDep, role: ClerkRole
) -> Envelope:
    try:
        item = container.discard_document(document_id, body.reason, actor=role)
    except DocumentNotFoundError as exc:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=document_id) from exc
    except DocumentAlreadyClosedError as exc:
        raise ApiError(409, "DOCUMENT_ALREADY_CLOSED", id=document_id) from exc
    return ok("DOCUMENT_DISCARDED", inbox_item_view(item))


outbox_router = APIRouter(prefix="/api", tags=["filing"])


@outbox_router.get("/outbox")
def list_outbox(container: ContainerDep, _: AnyRole) -> Envelope:
    return ok("OUTBOX_LISTED", [m.model_dump(mode="json") for m in container.list_outbox()])
