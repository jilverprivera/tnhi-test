"""SQLAlchemy persistence: SQLite on-prem, Postgres on Render (same schema)."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    email_file: Mapped[str] = mapped_column(String(200), index=True)
    position: Mapped[int] = mapped_column(Integer)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    proposal: Mapped[dict] = mapped_column(JSON)  # what the system proposed (never mutated)
    decision: Mapped[dict] = mapped_column(JSON)  # current decision (after human corrections)
    filing_number: Mapped[str | None] = mapped_column(String(40), nullable=True, unique=True)
    source_file: Mapped[bytes | None] = mapped_column(nullable=True)  # original attachment / .eml
    source_mime: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class LedgerRow(Base):
    __tablename__ = "ledger_entries"

    filing_number: Mapped[str] = mapped_column(String(40), primary_key=True)
    sequence: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    entry: Mapped[dict] = mapped_column(JSON)
    nit_key: Mapped[str] = mapped_column(String(30), index=True, default="")
    document_number_key: Mapped[str] = mapped_column(String(60), index=True, default="")
    due_date: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)


class AuditRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    actor: Mapped[str] = mapped_column(String(60))
    event: Mapped[str] = mapped_column(String(60), index=True)
    document_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class OutboxRow(Base):
    __tablename__ = "outbox_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    kind: Mapped[str] = mapped_column(String(40))
    document_id: Mapped[str] = mapped_column(String(200), index=True)
    to_address: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)


def build_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return engine


def build_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(engine, expire_on_commit=False)
