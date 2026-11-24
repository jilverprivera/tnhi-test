"""Use case: import e-mails into the filing inbox with a proposal for every document."""

from dataclasses import dataclass, field

from app.features.audit.application.ports import AuditLog
from app.features.filing.application.ports import InboxRepository
from app.features.filing.application.propose_filing import PendingInvoices, ProposeFiling
from app.features.filing.domain.inbox_item import InboxItem
from app.features.ingestion.application.ports import EmailReader
from app.features.ingestion.application.split_documents import SplitDocuments
from app.features.ingestion.domain.email_message import BODY_DOCUMENT_NAME, is_document
from app.features.ledger.domain.duplicates import invoice_key
from app.shared.domain.models import DocumentStatus, DocumentType


@dataclass
class ImportResult:
    imported: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # already imported
    failed: dict[str, str] = field(default_factory=dict)  # file -> error code


class ImportEmails:
    def __init__(
        self,
        reader: EmailReader,
        split: SplitDocuments,
        propose: ProposeFiling,
        inbox: InboxRepository,
        audit: AuditLog,
    ):
        self._reader, self._split, self._propose = reader, split, propose
        self._inbox, self._audit = inbox, audit

    def _pending_invoices(self) -> PendingInvoices:
        pending: PendingInvoices = {}
        for item in self._inbox.list():
            if item.status in (DocumentStatus.READY, DocumentStatus.NEEDS_REVIEW):
                data = item.proposal.data
                if item.decision.document_type == DocumentType.INVOICE and data.document_number:
                    pending[invoice_key(data.identification, data.document_number)] = item.id
        return pending

    def __call__(self, files: list[tuple[str, bytes]], actor: str) -> ImportResult:
        result = ImportResult()
        emails = []
        for name, content in files:
            try:
                emails.append((self._reader.read(content, name), content))
            except (ValueError, TypeError):  # malformed headers, e.g. a missing Date
                result.failed[name] = "EMAIL_UNREADABLE"
        pending = self._pending_invoices()
        for email, raw in sorted(emails, key=lambda e: e[0].sent_at):
            attachments = [a for a in email.attachments if is_document(a)]
            for document in self._split(email):
                if self._inbox.exists(document.id):
                    result.skipped.append(document.id)
                    continue
                proposal = self._propose(document, pending)
                item = InboxItem(
                    id=document.id,
                    status=proposal.status,
                    proposal=proposal,
                    decision=proposal.decision,
                    received_at=document.received_at,
                )
                if document.name == BODY_DOCUMENT_NAME:
                    source, mime = raw, "message/rfc822"
                else:
                    attachment = attachments[document.position]
                    source, mime = attachment.content, attachment.mime_type
                self._inbox.add(item, source, mime)
                self._audit.record(
                    "SYSTEM",
                    "DOCUMENT_PROPOSED",
                    document.id,
                    status=item.status.value,
                    reasons=proposal.decision.reason_codes(),
                )
                result.imported.append(document.id)
        self._audit.record(
            actor,
            "EMAILS_IMPORTED",
            None,
            imported=len(result.imported),
            skipped=len(result.skipped),
        )
        return result
