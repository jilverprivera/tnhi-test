"""The coordinator's verification of invoices held for possible fraud."""

import pytest
from openpyxl import load_workbook

from app.features.filing.application.verify_hold import (
    HoldNotPendingError,
    VerificationNoteRequiredError,
)
from app.features.filing.domain.inbox_item import HoldOutcome
from app.shared.domain.models import Department, LedgerStatus
from tests.conftest import inbox_files

HELD = "05.eml__0"


@pytest.fixture
def held(container):
    container.import_emails(inbox_files(), actor="TEST")
    container.escalate_hold(HELD, actor="CLERK")
    return container


def _ledger_entry(c):
    item = c.get_inbox_item(HELD)
    return c.ledger_repository.get(item.filing_number)


def test_held_invoice_waits_for_the_coordinator(held):
    states = {i.id: s for i, s in held.list_held_invoices()}
    assert states == {HELD: "AWAITING_VERIFICATION"}
    assert _ledger_entry(held).status == LedgerStatus.ON_HOLD


def test_before_martha_approves_it_is_still_with_the_clerk(container):
    container.import_emails(inbox_files(), actor="TEST")
    assert {i.id: s for i, s in container.list_held_invoices()} == {HELD: "PENDING_CLERK_APPROVAL"}
    with pytest.raises(HoldNotPendingError):
        container.verify_hold(HELD, HoldOutcome.RELEASED, "Llamé al proveedor", actor="COORDINATOR")


def test_release_sends_it_where_the_rules_would_have(held):
    item = held.verify_hold(
        HELD, HoldOutcome.RELEASED, "Confirmado por teléfono con tesorería", actor="COORDINATOR"
    )
    entry = _ledger_entry(held)
    assert item.hold_resolution.outcome == HoldOutcome.RELEASED
    # It carries OC-2026-0377, so it goes to Accounts payable, not to the coordinator any more
    assert (entry.status, entry.department) == (LedgerStatus.DELIVERED, Department.ACCOUNTS_PAYABLE)
    assert "VERIFIED_BY_PHONE" in entry.flags and "HOLD_FOR_VERIFICATION" not in entry.flags
    forward = [
        m for m in held.list_outbox() if m.document_id == HELD and m.kind == "FORWARD_TO_DEPARTMENT"
    ]
    assert forward and forward[0].to_address == "cxp@terminalesandinas.example"
    assert "cuenta registrada en el maestro" in forward[0].body


def test_reject_marks_fraud_and_warns_payables_and_procurement(held):
    held.verify_hold(
        HELD, HoldOutcome.REJECTED, "El proveedor no cambió de cuenta: fraude", actor="COORDINATOR"
    )
    entry = _ledger_entry(held)
    assert entry.status == LedgerStatus.REJECTED and "FRAUD_CONFIRMED" in entry.flags
    notices = {m.to_address for m in held.list_outbox() if m.kind == "FRAUD_CONFIRMED"}
    assert notices == {"cxp@terminalesandinas.example", "compras@terminalesandinas.example"}


def test_cannot_resolve_twice_or_without_a_note(held):
    with pytest.raises(VerificationNoteRequiredError):
        held.verify_hold(HELD, HoldOutcome.RELEASED, "ok", actor="COORDINATOR")
    held.verify_hold(HELD, HoldOutcome.REJECTED, "Fraude confirmado", actor="COORDINATOR")
    with pytest.raises(HoldNotPendingError):
        held.verify_hold(HELD, HoldOutcome.RELEASED, "Cambio de opinión", actor="COORDINATOR")


def test_resolution_is_audited_and_the_excel_row_is_updated(held):
    held.verify_hold(HELD, HoldOutcome.REJECTED, "Fraude confirmado", actor="COORDINATOR")
    events = [e for e in held.list_audit(HELD) if e["event"] == "HOLD_REJECTED"]
    assert events and events[0]["actor"] == "COORDINATOR"
    sheet = load_workbook(held.settings.data_dir / "libro-radicacion-2026.xlsx").worksheets[0]
    row = next(
        r for r in sheet.iter_rows(values_only=True) if r[0] == _ledger_entry(held).filing_number
    )
    assert row[10] == "Rechazada - fraude confirmado" and "NO PAGAR" in row[11]
    # historical rows are never rewritten
    assert next(sheet.iter_rows(min_row=2, max_row=2, values_only=True))[0] == "TAC-2026-ER-04790"
