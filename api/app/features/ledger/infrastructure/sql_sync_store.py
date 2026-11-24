"""Adapter: merge bases and last sync state, stored with SQLAlchemy."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.shared.infrastructure.db import LedgerSyncBaseRow, LedgerSyncStateRow


class SqlSyncStore:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def bases(self) -> dict[str, list[str]]:
        with self._sessions() as s:
            return {r.filing_number: list(r.cells) for r in s.scalars(select(LedgerSyncBaseRow))}

    def set_bases(self, bases: dict[str, list[str]]) -> None:
        with self._sessions.begin() as s:
            for filing_number, cells in bases.items():
                s.merge(LedgerSyncBaseRow(filing_number=filing_number, cells=cells))

    def state(self) -> dict | None:
        with self._sessions() as s:
            row = s.get(LedgerSyncStateRow, 1)
            return dict(row.payload) if row else None

    def set_state(self, state: dict) -> None:
        with self._sessions.begin() as s:
            s.merge(LedgerSyncStateRow(id=1, payload=state))
