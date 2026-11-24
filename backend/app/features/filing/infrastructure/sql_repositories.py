"""Adapters: inbox, outbox and audit log stored with SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import Decision, DocumentStatus, Proposal
from app.shared.infrastructure.db import DocumentRow, OutboxRow


def _to_item(row: DocumentRow) -> InboxItem:
    proposal = Proposal.model_validate(row.proposal)
    return InboxItem(
        id=row.id,
        status=DocumentStatus(row.status),
        proposal=proposal,
        decision=Decision.model_validate(row.decision),
        filing_number=row.filing_number,
        received_at=proposal.document.received_at,
        notes=row.decision.get("_notes", ""),
    )


def _decision_payload(item: InboxItem) -> dict:
    return item.decision.model_dump(mode="json") | {"_notes": item.notes}


class SqlInboxRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def exists(self, document_id: str) -> bool:
        with self._sessions() as s:
            return s.get(DocumentRow, document_id) is not None

    def add(self, item: InboxItem, source_file: bytes | None, source_mime: str) -> None:
        with self._sessions.begin() as s:
            s.add(
                DocumentRow(
                    id=item.id,
                    email_file=item.proposal.document.email_file,
                    position=item.proposal.document.position,
                    received_at=item.received_at,
                    status=item.status.value,
                    proposal=item.proposal.model_dump(mode="json"),
                    decision=_decision_payload(item),
                    filing_number=item.filing_number,
                    source_file=source_file,
                    source_mime=source_mime,
                )
            )

    def get(self, document_id: str) -> InboxItem | None:
        with self._sessions() as s:
            row = s.get(DocumentRow, document_id)
            return _to_item(row) if row else None

    def source_file(self, document_id: str) -> tuple[bytes, str] | None:
        with self._sessions() as s:
            row = s.get(DocumentRow, document_id)
            return (row.source_file, row.source_mime) if row and row.source_file else None

    def list(self, status: DocumentStatus | None = None) -> list[InboxItem]:
        query = select(DocumentRow).order_by(DocumentRow.received_at, DocumentRow.position)
        if status is not None:
            query = query.where(DocumentRow.status == status.value)
        with self._sessions() as s:
            return [_to_item(r) for r in s.scalars(query).all()]

    def update(self, item: InboxItem) -> None:
        with self._sessions.begin() as s:
            row = s.get(DocumentRow, item.id)
            row.status = item.status.value
            row.decision = _decision_payload(item)
            row.filing_number = item.filing_number


class SqlOutbox:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def put(self, message: OutboxMessage) -> None:
        with self._sessions.begin() as s:
            s.add(OutboxRow(**message.model_dump(mode="json")))

    def list(self) -> list[OutboxMessage]:
        with self._sessions() as s:
            rows = s.scalars(select(OutboxRow).order_by(OutboxRow.id)).all()
            return [
                OutboxMessage(
                    kind=r.kind,
                    document_id=r.document_id,
                    to_address=r.to_address,
                    subject=r.subject,
                    body=r.body,
                )
                for r in rows
            ]
