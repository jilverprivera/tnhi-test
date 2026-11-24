"""Retention use cases: the schedule, what is due, and the controlled disposal of a record."""

from collections.abc import Callable
from datetime import date

from pydantic import BaseModel

from app.features.audit.application.ports import AuditLog
from app.features.filing.application.ports import InboxRepository
from app.features.ledger.application.ports import LedgerRepository
from app.features.records.domain.retention import (
    DEFAULT_SCHEDULE,
    Disposition,
    RetentionRule,
    RetentionStatus,
    retention_ends,
    retention_status,
)
from app.shared.domain.models import DocumentType, LedgerEntry
from app.shared.domain.pagination import Page, PageRequest
from app.shared.domain.privacy import mask_personal_data


class RecordNotFoundError(LookupError):
    pass


class RetentionNotExpiredError(ValueError):
    pass


class DispositionNotAllowedError(ValueError):
    """The schedule says this record is conserved (or needs the committee's selection)."""


class RetentionView(BaseModel):
    filing_number: str
    document_type: DocumentType
    received_date: date
    retention_ends: date
    disposition: Disposition
    status: RetentionStatus


def _rule(entry: LedgerEntry) -> RetentionRule:
    return DEFAULT_SCHEDULE.get(entry.document_type, DEFAULT_SCHEDULE[DocumentType.OTHER])


def to_view(entry: LedgerEntry, today: date) -> RetentionView:
    rule = _rule(entry)
    return RetentionView(
        filing_number=entry.filing_number,
        document_type=entry.document_type,
        received_date=entry.received_date,
        retention_ends=retention_ends(entry, rule),
        disposition=rule.disposition,
        status=retention_status(entry, rule, today),
    )


class GetRetentionSchedule:
    def __call__(self) -> list[RetentionRule]:
        return list(DEFAULT_SCHEDULE.values())


class ListRetention:
    def __init__(self, ledger: LedgerRepository):
        self._ledger = ledger

    def __call__(
        self, today: date, status: RetentionStatus | None, request: PageRequest
    ) -> Page[RetentionView]:
        views = [to_view(e, today) for e in self._ledger.all_entries()]
        if status:
            views = [v for v in views if v.status == status]
        return Page.of(sorted(views, key=lambda v: v.retention_ends), request)


class DisposeRecord:
    """Disposal = the personal content goes away (original file and extracted text); the ledger row
    stays as the index of what existed and when it was destroyed, as the archive law requires."""

    def __init__(
        self,
        ledger: LedgerRepository,
        sync_ledger: Callable[[], object],
        inbox: InboxRepository,
        audit: AuditLog,
    ):
        self._ledger, self._sync, self._inbox, self._audit = ledger, sync_ledger, inbox, audit

    def __call__(
        self, filing_number: str, record_reference: str, today: date, actor: str
    ) -> RetentionView:
        entry = self._ledger.get(filing_number)
        if entry is None:
            raise RecordNotFoundError(filing_number)
        view = to_view(entry, today)
        if view.status != RetentionStatus.DUE_FOR_DISPOSITION:
            raise RetentionNotExpiredError(filing_number)
        if view.disposition != Disposition.DESTROY:
            raise DispositionNotAllowedError(filing_number)
        if entry.source_document_id:
            self._inbox.purge_content(entry.source_document_id)
        note = f"Eliminado {today.isoformat()} según TRD; acta {record_reference}".strip()
        updated = entry.model_copy(
            update={"flags": [*entry.flags, "DISPOSED"], "notes": f"{entry.notes} {note}".strip()}
        )
        self._ledger.update(updated)
        self._sync()
        self._audit.record(
            actor,
            "RECORD_DISPOSED",
            entry.source_document_id,
            filing_number=filing_number,
            record_reference=mask_personal_data(record_reference),
        )
        return to_view(updated, today)
