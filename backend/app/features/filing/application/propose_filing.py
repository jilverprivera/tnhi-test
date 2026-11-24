"""Use case: build the system's proposal for one document.

Resolves every lookup the rules need (supplier master, ledger, inbox) and hands the facts to
the pure domain rules.
"""

from app.features.catalogs.application.ports import CatalogSource
from app.features.classification.application.classify_document import ClassifyDocument
from app.features.classification.domain.field_extractor import (
    announces_account_change,
    bank_accounts,
)
from app.features.filing.domain.rules import FilingFacts, decide
from app.features.ledger.application.ports import LedgerRepository
from app.features.ledger.domain.duplicates import invoice_key
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.domain.models import Document, DocumentType, Proposal

PendingInvoices = dict[tuple[str, str], str]  # invoice key -> inbox document id


class ProposeFiling:
    def __init__(
        self,
        classify: ClassifyDocument,
        catalogs: CatalogSource,
        ledger: LedgerRepository,
        calendar: BusinessCalendar,
        min_ocr_confidence: float,
    ):
        self._classify = classify
        self._catalogs = catalogs
        self._ledger = ledger
        self._calendar = calendar
        self._min_ocr_confidence = min_ocr_confidence

    def __call__(self, document: Document, pending: PendingInvoices) -> Proposal:
        classified = self._classify(document)
        data = classified.data
        master = self._catalogs.supplier_master()

        supplier = master.by_nit(data.identification) if data.identification else None
        if supplier and not data.sender_name:
            data.sender_name = supplier.name

        existing, pending_of = None, None
        if classified.classification.document_type == DocumentType.INVOICE and data.document_number:
            existing = self._ledger.find_invoice(data.identification, data.document_number)
            key = invoice_key(data.identification, data.document_number)
            pending_of = pending.get(key) if not existing else None
            pending.setdefault(key, document.id)

        body_accounts = (
            bank_accounts(document.email_body) if document.email_body != document.text else []
        )
        facts = FilingFacts(
            document=document,
            classification=classified.classification,
            data=data,
            is_ambiguous=classified.is_ambiguous,
            supplier=supplier,
            sender_supplier=master.by_domain(document.sender),
            existing_filing_number=existing,
            pending_duplicate_of=pending_of,
            body_mentions_account=body_accounts[0][1] if body_accounts else "",
            body_announces_account_change=announces_account_change(document.email_body),
            calendar=self._calendar,
            min_ocr_confidence=self._min_ocr_confidence,
        )
        return Proposal(document=document, data=data, decision=decide(facts))
