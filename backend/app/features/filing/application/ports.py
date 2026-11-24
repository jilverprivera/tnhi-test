"""Filing ports."""

from typing import Protocol

from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import DocumentStatus


class InboxRepository(Protocol):
    def exists(self, document_id: str) -> bool: ...

    def add(self, item: InboxItem, source_file: bytes | None, source_mime: str) -> None: ...

    def get(self, document_id: str) -> InboxItem | None: ...

    def source_file(self, document_id: str) -> tuple[bytes, str] | None: ...

    def list(self, status: DocumentStatus | None = None) -> list[InboxItem]: ...

    def update(self, item: InboxItem) -> None: ...


class Outbox(Protocol):
    def put(self, message: OutboxMessage) -> None: ...

    def list(self) -> list[OutboxMessage]: ...
