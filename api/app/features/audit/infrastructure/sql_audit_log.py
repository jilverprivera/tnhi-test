"""Adapter: audit trail stored with SQLAlchemy. Append-only: no update or delete path exists."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.shared.infrastructure.db import AuditRow


class SqlAuditLog:
    """Append-only: there is no update or delete."""

    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def record(self, actor: str, event: str, document_id: str | None = None, **details) -> None:
        with self._sessions.begin() as s:
            s.add(AuditRow(actor=actor, event=event, document_id=document_id, details=details))

    def list(self, document_id: str | None = None) -> list[dict]:
        query = select(AuditRow).order_by(AuditRow.id)
        if document_id:
            query = query.where(AuditRow.document_id == document_id)
        with self._sessions() as s:
            return [
                {
                    "at": r.at.isoformat(),
                    "actor": r.actor,
                    "event": r.event,
                    "document_id": r.document_id,
                    "details": r.details,
                }
                for r in s.scalars(query).all()
            ]
