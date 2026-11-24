"""Read-side use cases of the filing inbox."""

from collections import Counter

from app.features.filing.application.ports import InboxRepository, Outbox
from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import DocumentStatus


class ListInbox:
    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(self, status: DocumentStatus | None = None) -> list[InboxItem]:
        return sorted(
            self._inbox.list(status), key=lambda i: (i.received_at, i.proposal.document.position)
        )


class InboxSummary:
    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(self) -> dict[str, int]:
        counts = Counter(i.status.value for i in self._inbox.list())
        return {s.value: counts.get(s.value, 0) for s in DocumentStatus}


class GetInboxItem:
    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(self, document_id: str) -> InboxItem | None:
        return self._inbox.get(document_id)


class ListOutbox:
    def __init__(self, outbox: Outbox):
        self._outbox = outbox

    def __call__(self) -> list[OutboxMessage]:
        return self._outbox.list()
