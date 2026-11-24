"""Audit port: an append-only trail of who did what, used by every mutating use case."""

from typing import Protocol


class AuditLog(Protocol):
    def record(self, actor: str, event: str, document_id: str | None = None, **details) -> None: ...

    def list(self, document_id: str | None = None) -> list[dict]: ...
