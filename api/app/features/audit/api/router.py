"""Audit trail endpoint (read-only)."""

from fastapi import APIRouter

from app.shared.infrastructure.http import AnyRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit(container: ContainerDep, _: AnyRole, document_id: str | None = None) -> Envelope:
    return ok("AUDIT_LISTED", container.list_audit(document_id))
