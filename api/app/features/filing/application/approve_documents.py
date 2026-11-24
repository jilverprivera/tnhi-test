"""Use case: the clerk approves proposals; only then filing numbers are assigned.

Numbers follow reception order (and attachment order inside an e-mail). Assignment is
serialized with a lock, and the database's unique constraint is the last line of defense.
"""

import threading
from collections.abc import Callable

from app.features.audit.application.ports import AuditLog
from app.features.catalogs.application.ports import CatalogSource
from app.features.filing.application.ports import InboxRepository, Outbox
from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.ledger_entry_factory import build_ledger_entry
from app.features.filing.domain.outbox_composer import compose
from app.features.ledger.application.ports import LedgerRepository
from app.features.ledger.domain.filing_number import format_filing_number
from app.shared.domain.models import Action, Department, DocumentStatus

_SEQUENCE_LOCK = threading.Lock()


class DocumentNotFoundError(LookupError):
    pass


class DocumentNotApprovableError(ValueError):
    """Raised when a document still needs review and the caller only approves ready ones."""


class HoldRequiresEscalationError(ValueError):
    """A suspected-fraud invoice is never 'approved': the clerk alerts the coordinator instead."""


class NotAHoldError(ValueError):
    """Only invoices held for possible fraud are escalated to the coordinator."""


class DecisionIncompleteError(ValueError):
    """A document cannot be filed without a real department (e.g. it was unreadable)."""


class ApproveDocuments:
    def __init__(
        self,
        inbox: InboxRepository,
        ledger: LedgerRepository,
        sync_ledger: Callable[[], object],
        outbox: Outbox,
        audit: AuditLog,
        catalogs: CatalogSource,
        prefix: str,
    ):
        self._inbox, self._ledger, self._sync = inbox, ledger, sync_ledger
        self._outbox, self._audit, self._catalogs = outbox, audit, catalogs
        self._prefix = prefix

    def _load(self, ids: list[str], allow_review: bool, escalate_holds: bool) -> list[InboxItem]:
        items = []
        for document_id in ids:
            item = self._inbox.get(document_id)
            if item is None:
                raise DocumentNotFoundError(document_id)
            if item.status in (DocumentStatus.APPROVED, DocumentStatus.DISCARDED):
                continue
            if item.status == DocumentStatus.NEEDS_REVIEW and not allow_review:
                raise DocumentNotApprovableError(document_id)
            if item.decision.action == Action.HOLD_FOR_VERIFICATION and not escalate_holds:
                raise HoldRequiresEscalationError(document_id)
            if item.decision.is_fileable and item.decision.department == Department.NONE:
                raise DecisionIncompleteError(document_id)
            items.append(item)
        return sorted(items, key=lambda i: (i.received_at, i.proposal.document.position))

    def __call__(
        self, ids: list[str], actor: str, allow_review: bool = True, escalate_holds: bool = False
    ) -> list[InboxItem]:
        """Approves in reception order. Held invoices are only processed with `escalate_holds`:
        they get a filing number for traceability, stay ON_HOLD and alert the coordinator."""
        departments = self._catalogs.departments()
        with _SEQUENCE_LOCK:
            # Rows typed by hand in the shared Excel first: the consecutive must continue after them
            self._sync()
            approved = []
            for item in self._load(ids, allow_review, escalate_holds):
                if item.decision.is_fileable:
                    sequence = self._ledger.last_sequence() + 1
                    item.filing_number = format_filing_number(self._prefix, sequence)
                    self._ledger.append(build_ledger_entry(item, item.filing_number), sequence)
                item.status = DocumentStatus.APPROVED
                self._inbox.update(item)
                for message in compose(item, departments):
                    self._outbox.put(message)
                is_hold = item.decision.action == Action.HOLD_FOR_VERIFICATION
                self._audit.record(
                    actor,
                    "HOLD_ESCALATED" if is_hold else "DOCUMENT_APPROVED",
                    item.id,
                    filing_number=item.filing_number,
                    action=item.decision.action.value,
                    department=item.decision.department.value,
                    corrected=item.was_corrected,
                )
                approved.append(item)
            if any(i.filing_number for i in approved):
                self._sync()
        return approved


class ApproveReadyDocuments:
    """Batch approval: only what the system is sure about (status READY)."""

    def __init__(self, inbox: InboxRepository, approve: ApproveDocuments):
        self._inbox, self._approve = inbox, approve

    def __call__(self, actor: str) -> list[InboxItem]:
        ready = [
            i.id
            for i in self._inbox.list(DocumentStatus.READY)
            if i.decision.action
            != Action.HOLD_FOR_VERIFICATION  # never in bulk: one by one, with an alert
        ]
        return self._approve(ready, actor, allow_review=False)


class EscalateHold:
    """The clerk alerts the coordinator about a suspected-fraud invoice (interview: "se la paso a
    la doctora Claudia para que verifiquen por teléfono"). Nothing is sent to payment."""

    def __init__(self, inbox: InboxRepository, approve: ApproveDocuments):
        self._inbox, self._approve = inbox, approve

    def __call__(self, document_id: str, actor: str) -> InboxItem:
        item = self._inbox.get(document_id)
        if item is None:
            raise DocumentNotFoundError(document_id)
        if item.decision.action != Action.HOLD_FOR_VERIFICATION:
            raise NotAHoldError(document_id)
        escalated = self._approve([document_id], actor, escalate_holds=True)
        return escalated[0] if escalated else self._inbox.get(document_id)
