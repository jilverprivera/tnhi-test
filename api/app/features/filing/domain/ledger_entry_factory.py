"""Builds the ledger row for an approved inbox item."""

from app.features.filing.domain.inbox_item import InboxItem
from app.shared.domain.models import Action, DocumentType, LedgerEntry, LedgerStatus

LEDGER_FLAGS = {
    "TRAVEL_REQUEST_LATE",
    "SUPPLIER_NOT_REGISTERED",
    "INVOICE_WITHOUT_PURCHASE_ORDER",
    "INVOICE_ACCOUNT_MISMATCH",
    "SENDER_DOMAIN_MISMATCH",
    "ACCOUNT_CHANGE_ANNOUNCED",
    "TUTELA_THREAT",
}


def ledger_subject(item: InboxItem) -> str:
    data, document = item.proposal.data, item.proposal.document
    if item.decision.document_type == DocumentType.INVOICE and data.document_number:
        return f"Factura {data.document_number}"
    return document.email_subject


def build_ledger_entry(item: InboxItem, filing_number: str) -> LedgerEntry:
    decision, data, document = item.decision, item.proposal.data, item.proposal.document
    flags = [r.code for r in decision.reasons if r.code in LEDGER_FLAGS]
    if decision.action == Action.HOLD_FOR_VERIFICATION:
        flags.append("HOLD_FOR_VERIFICATION")
        status = LedgerStatus.ON_HOLD
    elif decision.due_date:
        status = LedgerStatus.IN_PROGRESS
    else:
        status = LedgerStatus.DELIVERED
    return LedgerEntry(
        filing_number=filing_number,
        received_date=document.received_at.date(),
        sender=data.sender_name or document.sender_name,
        identification=data.identification or document.sender,
        document_type=decision.document_type,
        subject=ledger_subject(item),
        document_number=data.document_number,
        total_amount=data.total_amount,
        department=decision.department,
        due_date=decision.due_date,
        status=status,
        notes=" ".join(filter(None, [data.purchase_order, item.notes])),
        flags=flags,
        urgent=decision.urgent,
        source_document_id=item.id,
    )
