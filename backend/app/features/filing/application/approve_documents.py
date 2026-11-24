"""Use case: the clerk approves proposals; only then filing numbers are assigned.

Numbers follow reception order (and attachment order inside an e-mail). Assignment is
serialized with a lock, and the database's unique constraint is the last line of defense.
"""

import threading

from app.features.audit.application.ports import AuditLog
from app.features.catalogs.application.ports import CatalogSource
from app.features.filing.application.ports import InboxRepository, Outbox
from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.ledger_entry_factory import build_ledger_entry
from app.features.filing.domain.outbox_composer import compose
from app.features.ledger.application.ports import LedgerRepository, LedgerWorkbook
from app.features.ledger.domain.filing_number import format_filing_number
from app.shared.domain.models import Department, DocumentStatus

_SEQUENCE_LOCK = threading.Lock()


class DocumentNotFoundError(LookupError):
    pass


class DocumentNotApprovableError(ValueError):
    """Raised when a document still needs review and the caller only approves ready ones."""


class DecisionIncompleteError(ValueError):
    """A document cannot be filed without a real department (e.g. it was unreadable)."""


class ApproveDocuments:
    def __init__(
        self,
        inbox: InboxRepository,
        ledger: LedgerRepository,
        workbook: LedgerWorkbook,
        outbox: Outbox,
        audit: AuditLog,
        catalogs: CatalogSource,
        prefix: str,
    ):
        self._inbox, self._ledger, self._workbook = inbox, ledger, workbook
        self._outbox, self._audit, self._catalogs = outbox, audit, catalogs
        self._prefix = prefix

    def _load(self, ids: list[str], allow_review: bool) -> list[InboxItem]:
        items = []
        for document_id in ids:
            item = self._inbox.get(document_id)
            if item is None:
                raise DocumentNotFoundError(document_id)
            if item.status in (DocumentStatus.APPROVED, DocumentStatus.DISCARDED):
                continue
            if item.status == DocumentStatus.NEEDS_REVIEW and not allow_review:
                raise DocumentNotApprovableError(document_id)
            if item.decision.is_fileable and item.decision.department == Department.NONE:
                raise DecisionIncompleteError(document_id)
            items.append(item)
        return sorted(items, key=lambda i: (i.received_at, i.proposal.document.position))

    def __call__(self, ids: list[str], actor: str, allow_review: bool = True) -> list[InboxItem]:
        departments = self._catalogs.departments()
        with _SEQUENCE_LOCK:
            approved = []
            for item in self._load(ids, allow_review):
                if item.decision.is_fileable:
                    sequence = self._ledger.last_sequence() + 1
                    item.filing_number = format_filing_number(self._prefix, sequence)
                    self._ledger.append(build_ledger_entry(item, item.filing_number), sequence)
                item.status = DocumentStatus.APPROVED
                self._inbox.update(item)
                for message in compose(item, departments):
                    self._outbox.put(message)
                self._audit.record(
                    actor,
                    "DOCUMENT_APPROVED",
                    item.id,
                    filing_number=item.filing_number,
                    action=item.decision.action.value,
                    department=item.decision.department.value,
                    corrected=item.was_corrected,
                )
                approved.append(item)
            if any(i.filing_number for i in approved):
                self._workbook.save(self._ledger.all_entries())
        return approved


class ApproveReadyDocuments:
    """Batch approval: only what the system is sure about (status READY)."""

    def __init__(self, inbox: InboxRepository, approve: ApproveDocuments):
        self._inbox, self._approve = inbox, approve

    def __call__(self, actor: str) -> list[InboxItem]:
        ready = [i.id for i in self._inbox.list(DocumentStatus.READY)]
        return self._approve(ready, actor, allow_review=False)
