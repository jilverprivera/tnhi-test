"""Adapter: ledger stored with SQLAlchemy (source of truth; the Excel is a synchronized view)."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.features.ledger.domain.duplicates import invoice_key
from app.shared.domain.models import DocumentType, LedgerEntry
from app.shared.infrastructure.db import LedgerRow


class SqlLedgerRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def is_empty(self) -> bool:
        with self._sessions() as s:
            return s.scalar(select(func.count()).select_from(LedgerRow)) == 0

    def all_entries(self) -> list[LedgerEntry]:
        with self._sessions() as s:
            rows = s.scalars(select(LedgerRow).order_by(LedgerRow.sequence)).all()
            return [LedgerEntry.model_validate(r.entry) for r in rows]

    def find_invoice(self, nit: str, document_number: str) -> str | None:
        nit_key, number_key = invoice_key(nit, document_number)
        with self._sessions() as s:
            rows = s.scalars(
                select(LedgerRow)
                .where(LedgerRow.nit_key == nit_key, LedgerRow.document_number_key == number_key)
                .order_by(LedgerRow.sequence)
            ).all()
            for row in rows:
                if row.entry.get("document_type") == DocumentType.INVOICE:
                    return row.filing_number
        return None

    def last_sequence(self) -> int:
        with self._sessions() as s:
            return s.scalar(select(func.max(LedgerRow.sequence))) or 0

    def append(self, entry: LedgerEntry, sequence: int) -> None:
        nit_key, number_key = invoice_key(entry.identification, entry.document_number)
        with self._sessions.begin() as s:
            s.add(
                LedgerRow(
                    filing_number=entry.filing_number,
                    sequence=sequence,
                    entry=entry.model_dump(mode="json"),
                    nit_key=nit_key,
                    document_number_key=number_key,
                    due_date=entry.due_date.isoformat() if entry.due_date else None,
                )
            )

    def get(self, filing_number: str) -> LedgerEntry | None:
        with self._sessions() as s:
            row = s.get(LedgerRow, filing_number)
            return LedgerEntry.model_validate(row.entry) if row else None

    def update(self, entry: LedgerEntry) -> None:
        with self._sessions.begin() as s:
            row = s.get(LedgerRow, entry.filing_number)
            row.entry = entry.model_dump(mode="json")
            row.due_date = entry.due_date.isoformat() if entry.due_date else None

    def due_between(self, start: date, end: date) -> list[LedgerEntry]:
        with self._sessions() as s:
            rows = s.scalars(
                select(LedgerRow)
                .where(LedgerRow.due_date.is_not(None), LedgerRow.due_date >= start.isoformat())
                .where(LedgerRow.due_date <= end.isoformat())
                .order_by(LedgerRow.due_date)
            ).all()
            return [LedgerEntry.model_validate(r.entry) for r in rows]
