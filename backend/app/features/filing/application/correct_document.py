"""Use case: the clerk corrects a proposal. The original proposal is kept for audit."""

from datetime import date

from pydantic import BaseModel

from app.features.audit.application.ports import AuditLog
from app.features.filing.application.approve_documents import DocumentNotFoundError
from app.features.filing.application.ports import InboxRepository
from app.features.filing.domain.inbox_item import InboxItem
from app.shared.domain.models import Action, Department, DocumentStatus, DocumentType, Reason


class DocumentAlreadyClosedError(ValueError):
    pass


class Correction(BaseModel):
    document_type: DocumentType | None = None
    department: Department | None = None
    action: Action | None = None
    due_date: date | None = None
    clear_due_date: bool = False
    urgent: bool | None = None
    notes: str | None = None


class CorrectDocument:
    def __init__(self, inbox: InboxRepository, audit: AuditLog):
        self._inbox, self._audit = inbox, audit

    def __call__(self, document_id: str, correction: Correction, actor: str) -> InboxItem:
        item = self._inbox.get(document_id)
        if item is None:
            raise DocumentNotFoundError(document_id)
        if item.status in (DocumentStatus.APPROVED, DocumentStatus.DISCARDED):
            raise DocumentAlreadyClosedError(document_id)

        decision = item.decision.model_copy(deep=True)
        changes = correction.model_dump(exclude_none=True, exclude={"clear_due_date", "notes"})
        for field, value in changes.items():
            setattr(decision, field, value)
        if correction.clear_due_date:
            decision.due_date = None
            changes["due_date"] = None
        # A person reviewed it: blocking reasons are resolved, but kept for traceability
        decision.reasons = [r.model_copy(update={"blocking": False}) for r in decision.reasons]
        decision.reasons.append(
            Reason(code="REVIEWED_BY_HUMAN", params={"fields": ",".join(sorted(changes)) or "NONE"})
        )
        item.decision = decision
        if correction.notes is not None:
            item.notes = correction.notes
        item.status = DocumentStatus.READY
        self._inbox.update(item)
        self._audit.record(
            actor,
            "DOCUMENT_CORRECTED",
            document_id,
            changes={k: str(v) for k, v in changes.items()},
        )
        return item


class DiscardDocument:
    def __init__(self, inbox: InboxRepository, audit: AuditLog):
        self._inbox, self._audit = inbox, audit

    def __call__(self, document_id: str, reason: str, actor: str) -> InboxItem:
        item = self._inbox.get(document_id)
        if item is None:
            raise DocumentNotFoundError(document_id)
        if item.status == DocumentStatus.APPROVED:
            raise DocumentAlreadyClosedError(document_id)
        item.status = DocumentStatus.DISCARDED
        item.notes = reason
        self._inbox.update(item)
        self._audit.record(actor, "DOCUMENT_DISCARDED", document_id, reason=reason)
        return item
