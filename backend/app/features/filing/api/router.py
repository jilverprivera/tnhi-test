"""Filing inbox endpoints (driving adapter)."""

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from app.features.filing.api.views import inbox_item_view
from app.features.filing.application.approve_documents import (
    DecisionIncompleteError,
    DocumentNotApprovableError,
    DocumentNotFoundError,
)
from app.features.filing.application.correct_document import Correction, DocumentAlreadyClosedError
from app.shared.domain.models import DocumentStatus
from app.shared.infrastructure.http import AnyRole, ApiError, ClerkRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/inbox", tags=["filing"])


class ApproveRequest(BaseModel):
    ids: list[str]


class DiscardRequest(BaseModel):
    reason: str


@router.get("")
def list_inbox(
    container: ContainerDep, _: AnyRole, status: DocumentStatus | None = None
) -> Envelope:
    items = container.list_inbox(status)
    return ok("INBOX_LISTED", [inbox_item_view(i) for i in items])


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
    return ok("DOCUMENTS_APPROVED", [inbox_item_view(i) for i in approved])


@router.post("/approve-ready")
def approve_ready(container: ContainerDep, role: ClerkRole) -> Envelope:
    try:
        approved = container.approve_ready(actor=role)
    except DocumentNotApprovableError as exc:
        raise ApiError(409, "DOCUMENT_NEEDS_REVIEW", id=str(exc)) from exc
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
