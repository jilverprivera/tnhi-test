"""Duplicate detection keys: same supplier (NIT) and same document number."""

from collections import defaultdict

from app.shared.domain.identifiers import normalize_document_number, normalize_nit
from app.shared.domain.models import DocumentType, LedgerEntry


def invoice_key(nit: str, document_number: str) -> tuple[str, str]:
    return normalize_nit(nit), normalize_document_number(document_number)


def historical_duplicates(entries: list[LedgerEntry]) -> list[list[str]]:
    """Groups of filing numbers that share supplier + invoice number in the ledger."""
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for e in entries:
        if e.document_type == DocumentType.INVOICE and e.identification and e.document_number:
            groups[invoice_key(e.identification, e.document_number)].append(e.filing_number)
    return [numbers for numbers in groups.values() if len(numbers) > 1]
