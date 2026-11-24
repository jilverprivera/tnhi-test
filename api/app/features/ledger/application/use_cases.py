"""Ledger use cases: seed from the client's Excel, query, export, and detect duplicates."""

from dataclasses import dataclass

from app.features.ledger.application.ports import LedgerRepository, LedgerWorkbook
from app.features.ledger.domain.duplicates import historical_duplicates
from app.features.ledger.domain.filing_number import parse_sequence
from app.shared.domain.models import LedgerEntry
from app.shared.domain.pagination import Page, PageRequest


class SeedLedger:
    """On first boot, the historical Excel becomes the starting point of the ledger."""

    def __init__(self, repository: LedgerRepository, workbook: LedgerWorkbook, prefix: str):
        self._repository, self._workbook, self._prefix = repository, workbook, prefix

    def __call__(self) -> int:
        if not self._repository.is_empty():
            return 0
        entries = self._workbook.read()
        for entry in entries:
            sequence = parse_sequence(entry.filing_number, self._prefix)
            if sequence is not None:
                self._repository.append(entry, sequence)
        return len(entries)


@dataclass(frozen=True)
class LedgerQuery:
    text: str = ""
    department: str = ""
    document_type: str = ""


class ListLedger:
    def __init__(self, repository: LedgerRepository):
        self._repository = repository

    def __call__(self, query: LedgerQuery) -> list[LedgerEntry]:
        needle = query.text.strip().lower()
        result = []
        for e in self._repository.all_entries():
            if query.department and e.department != query.department:
                continue
            if query.document_type and e.document_type != query.document_type:
                continue
            haystack = (
                f"{e.filing_number} {e.sender} {e.identification} {e.subject} {e.document_number}"
            )
            if needle and needle not in haystack.lower():
                continue
            result.append(e)
        return sorted(result, key=lambda e: e.filing_number, reverse=True)


class PaginateLedger:
    def __init__(self, list_ledger: ListLedger):
        self._list = list_ledger

    def __call__(self, query: LedgerQuery, request: PageRequest) -> Page[LedgerEntry]:
        return Page.of(self._list(query), request)


class ExportLedger:
    """The shared Excel as it is after syncing; if someone has it open, a copy rendered from the ledger."""

    def __init__(self, repository: LedgerRepository, workbook: LedgerWorkbook, sync_ledger):
        self._repository, self._workbook, self._sync = repository, workbook, sync_ledger

    def __call__(self) -> bytes:
        state = self._sync()
        if getattr(state, "outcome", None) == "LOCKED":
            return self._workbook.render(self._repository.all_entries())
        return self._workbook.file_bytes()


class FindLedgerDuplicates:
    def __init__(self, repository: LedgerRepository):
        self._repository = repository

    def __call__(self) -> list[list[str]]:
        return historical_duplicates(self._repository.all_entries())
