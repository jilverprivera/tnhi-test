"""Read-side use cases of the filing inbox."""

from collections import Counter
from collections.abc import Sequence

from app.features.filing.application.ports import InboxRepository, Outbox
from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import DocumentStatus
from app.shared.domain.pagination import Page, PageRequest


class ListInbox:
    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(self, status: DocumentStatus | None = None) -> list[InboxItem]:
        return sorted(
            self._inbox.list(status), key=lambda i: (i.received_at, i.proposal.document.position)
        )


class PaginateInbox:
    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(
        self, statuses: Sequence[DocumentStatus] | None, request: PageRequest
    ) -> Page[InboxItem]:
        return self._inbox.page(statuses, request)


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


class VerificationState:
    PENDING_CLERK_APPROVAL = "PENDING_CLERK_APPROVAL"  # still in Martha's inbox
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"  # filed and held: the coordinator must call
    RELEASED = "RELEASED"
    REJECTED = "REJECTED"


def verification_state(item: InboxItem) -> str:
    if item.hold_resolution is not None:
        return item.hold_resolution.outcome.value
    if item.status == DocumentStatus.APPROVED:
        return VerificationState.AWAITING_VERIFICATION
    return VerificationState.PENDING_CLERK_APPROVAL


class ListHeldInvoices:
    """Every invoice the rules held for possible fraud, with where it stands."""

    def __init__(self, inbox: InboxRepository):
        self._inbox = inbox

    def __call__(self) -> list[tuple[InboxItem, str]]:
        held = [
            i
            for i in self._inbox.list()
            if i.decision.action == "HOLD_FOR_VERIFICATION" and i.status != DocumentStatus.DISCARDED
        ]
        return [(i, verification_state(i)) for i in sorted(held, key=lambda i: i.received_at)]
