"""Filing ports."""

from collections.abc import Sequence
from typing import Protocol

from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import DocumentStatus
from app.shared.domain.pagination import Page, PageRequest


class InboxRepository(Protocol):
    def exists(self, document_id: str) -> bool: ...

    def add(self, item: InboxItem, source_file: bytes | None, source_mime: str) -> None: ...

    def get(self, document_id: str) -> InboxItem | None: ...

    def source_file(self, document_id: str) -> tuple[bytes, str] | None: ...

    def list(self, status: DocumentStatus | None = None) -> list[InboxItem]: ...

    def update(self, item: InboxItem) -> None: ...

    def page(
        self, statuses: Sequence[DocumentStatus] | None, request: PageRequest
    ) -> Page[InboxItem]: ...

    def purge_content(self, document_id: str) -> bool: ...


class Outbox(Protocol):
    def put(self, message: OutboxMessage) -> None: ...

    def list(self) -> list[OutboxMessage]: ...
