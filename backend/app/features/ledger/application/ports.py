"""Ledger ports."""

from datetime import date
from typing import Protocol

from app.shared.domain.models import LedgerEntry


class LedgerRepository(Protocol):
    def is_empty(self) -> bool: ...

    def all_entries(self) -> list[LedgerEntry]: ...

    def find_invoice(self, nit: str, document_number: str) -> str | None: ...

    def last_sequence(self) -> int: ...

    def append(self, entry: LedgerEntry, sequence: int) -> None: ...

    def due_between(self, start: date, end: date) -> list[LedgerEntry]: ...


class LedgerWorkbook(Protocol):
    """The client's Excel file: the format Accounting and Legal already use."""

    def read(self) -> list[LedgerEntry]: ...

    def render(self, entries: list[LedgerEntry]) -> bytes: ...

    def save(self, entries: list[LedgerEntry]) -> None: ...
