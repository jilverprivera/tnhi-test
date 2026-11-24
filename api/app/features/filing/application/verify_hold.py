"""Use case: the coordinator resolves an invoice held for possible fraud.

Business rule (interview): "si la cuenta de la factura no es la que está en el maestro, o el correo
llega de una dirección rara, no la mando a ningún lado: se la paso a la doctora Claudia para que
verifiquen por teléfono con el proveedor". After that phone call she either releases the invoice
(it continues to the department that would have received it) or confirms the fraud (never paid).
"""

from collections.abc import Callable
from datetime import UTC, datetime

from app.features.audit.application.ports import AuditLog
from app.features.catalogs.application.ports import CatalogSource
from app.features.filing.application.approve_documents import DocumentNotFoundError
from app.features.filing.application.ports import InboxRepository, Outbox
from app.features.filing.domain.inbox_item import HoldOutcome, HoldResolution, InboxItem
from app.features.filing.domain.outbox_composer import compose_hold_rejected, compose_hold_released
from app.features.ledger.application.ports import LedgerRepository
from app.shared.domain.models import Department, LedgerStatus

MIN_NOTE_LENGTH = 5


class HoldNotPendingError(ValueError):
    """The document is not an approved, held invoice waiting for verification."""


class VerificationNoteRequiredError(ValueError):
    pass


def release_department(item: InboxItem) -> Department:
    """Where the invoice would have gone without the hold: Martha's purchase-order rule."""
    return (
        Department.ACCOUNTS_PAYABLE if item.proposal.data.purchase_order else Department.PROCUREMENT
    )


class VerifyHold:
    def __init__(
        self,
        inbox: InboxRepository,
        ledger: LedgerRepository,
        sync_ledger: Callable[[], object],
        outbox: Outbox,
        audit: AuditLog,
        catalogs: CatalogSource,
    ):
        self._inbox, self._ledger, self._sync = inbox, ledger, sync_ledger
        self._outbox, self._audit, self._catalogs = outbox, audit, catalogs

    def __call__(self, document_id: str, outcome: HoldOutcome, note: str, actor: str) -> InboxItem:
        if len(note.strip()) < MIN_NOTE_LENGTH:
            raise VerificationNoteRequiredError(document_id)
        item = self._inbox.get(document_id)
        if item is None:
            raise DocumentNotFoundError(document_id)
        entry = self._ledger.get(item.filing_number) if item.filing_number else None
        if (
            not item.is_awaiting_verification
            or entry is None
            or entry.status != LedgerStatus.ON_HOLD
        ):
            raise HoldNotPendingError(document_id)

        departments = self._catalogs.departments()
        flags = [f for f in entry.flags if f != "HOLD_FOR_VERIFICATION"]
        if outcome == HoldOutcome.RELEASED:
            department = release_department(item)
            entry = entry.model_copy(
                update={
                    "status": LedgerStatus.DELIVERED,
                    "department": department,
                    "flags": [*flags, "VERIFIED_BY_PHONE"],
                }
            )
            messages = compose_hold_released(item, department, departments, note.strip())
        else:
            entry = entry.model_copy(
                update={"status": LedgerStatus.REJECTED, "flags": [*flags, "FRAUD_CONFIRMED"]}
            )
            messages = compose_hold_rejected(item, departments, note.strip())

        item.hold_resolution = HoldResolution(
            outcome=outcome, note=note.strip(), actor=actor, at=datetime.now(UTC)
        )
        self._ledger.update(entry)
        self._inbox.update(item)
        for message in messages:
            self._outbox.put(message)
        self._sync()
        self._audit.record(
            actor,
            "HOLD_RELEASED" if outcome == HoldOutcome.RELEASED else "HOLD_REJECTED",
            document_id,
            filing_number=item.filing_number,
            department=entry.department.value,
        )
        return item
