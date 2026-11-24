"""Held-invoice verification endpoints: the coordinator releases or rejects after calling the supplier."""

from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from app.features.filing.api.views import inbox_item_view
from app.features.filing.application.approve_documents import DocumentNotFoundError
from app.features.filing.application.verify_hold import (
    HoldNotPendingError,
    VerificationNoteRequiredError,
    release_department,
)
from app.features.filing.domain.inbox_item import HoldOutcome, InboxItem
from app.shared.infrastructure.http import (
    AnyRole,
    ApiError,
    ContainerDep,
    CoordinatorRole,
    Envelope,
    ok,
)

router = APIRouter(prefix="/api/verifications", tags=["filing"])


class VerificationRequest(BaseModel):
    note: str


def _view(item: InboxItem, state: str, container) -> dict:
    supplier = container.catalogs.supplier_master().by_nit(item.proposal.data.identification)
    return inbox_item_view(item) | {
        "verification_state": state,
        "release_department": release_department(item),
        "hold_resolution": item.hold_resolution.model_dump(mode="json")
        if item.hold_resolution
        else None,
        "master_supplier": asdict(supplier) | {"is_active": supplier.is_active}
        if supplier
        else None,
    }


@router.get("")
def list_verifications(container: ContainerDep, _: AnyRole) -> Envelope:
    return ok(
        "VERIFICATIONS_LISTED", [_view(i, s, container) for i, s in container.list_held_invoices()]
    )


def _resolve(
    document_id: str, outcome: HoldOutcome, body: VerificationRequest, container, role
) -> Envelope:
    try:
        item = container.verify_hold(document_id, outcome, body.note, actor=role)
    except DocumentNotFoundError as exc:
        raise ApiError(404, "DOCUMENT_NOT_FOUND", id=document_id) from exc
    except VerificationNoteRequiredError as exc:
        raise ApiError(422, "VERIFICATION_NOTE_REQUIRED", id=document_id) from exc
    except HoldNotPendingError as exc:
        raise ApiError(409, "HOLD_NOT_PENDING", id=document_id) from exc
    code = "HOLD_RELEASED" if outcome == HoldOutcome.RELEASED else "HOLD_REJECTED"
    return ok(code, _view(item, outcome.value, container))


@router.post("/{document_id}/release")
def release(
    document_id: str, body: VerificationRequest, container: ContainerDep, role: CoordinatorRole
) -> Envelope:
    return _resolve(document_id, HoldOutcome.RELEASED, body, container, role)


@router.post("/{document_id}/reject")
def reject(
    document_id: str, body: VerificationRequest, container: ContainerDep, role: CoordinatorRole
) -> Envelope:
    return _resolve(document_id, HoldOutcome.REJECTED, body, container, role)
