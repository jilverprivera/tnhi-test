"""Adapters: inbox, outbox and audit log stored with SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.features.filing.domain.inbox_item import HoldResolution, InboxItem
from app.features.filing.domain.outbox_message import OutboxMessage
from app.shared.domain.models import Decision, DocumentStatus, Proposal
from app.shared.domain.pagination import Page, PageRequest
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
        hold_resolution=HoldResolution.model_validate(hold)
        if (hold := row.decision.get("_hold"))
        else None,
    )


def _decision_payload(item: InboxItem) -> dict:
    hold = item.hold_resolution.model_dump(mode="json") if item.hold_resolution else None
    return item.decision.model_dump(mode="json") | {"_notes": item.notes, "_hold": hold}


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

    def page(
        self, statuses: Sequence[DocumentStatus] | None, request: PageRequest
    ) -> Page[InboxItem]:
        r = request.clamp()
        query = select(DocumentRow)
        if statuses:
            query = query.where(DocumentRow.status.in_([s.value for s in statuses]))
        with self._sessions() as s:
            total = s.scalar(select(func.count()).select_from(query.subquery())) or 0
            rows = s.scalars(
                query.order_by(DocumentRow.received_at, DocumentRow.position)
                .limit(r.limit)
                .offset(r.offset)
            ).all()
            return Page(
                items=[_to_item(row) for row in rows], total=total, limit=r.limit, offset=r.offset
            )

    def purge_content(self, document_id: str) -> bool:
        """Removes the original file and the extracted text (retention disposal); keeps the decision."""
        with self._sessions.begin() as s:
            row = s.get(DocumentRow, document_id)
            if row is None:
                return False
            proposal = dict(row.proposal)
            proposal["document"] = {**proposal["document"], "text": "", "email_body": ""}
            row.proposal = proposal
            row.source_file = None
            return True

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
