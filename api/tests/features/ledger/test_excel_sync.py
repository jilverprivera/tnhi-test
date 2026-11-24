"""Bidirectional sync with the shared Excel: nobody's work is lost, nothing collides."""

from datetime import date

from openpyxl import load_workbook

from app.features.ledger.application.sync_ledger import SyncOutcome
from app.features.ledger.infrastructure.excel_ledger import WorkbookChangedError
from tests.conftest import inbox_files

TODAY = date(2026, 11, 18)


def _excel(container):
    return container.settings.data_dir / "libro-radicacion-2026.xlsx"


def _person_edits(container, edit):
    """What Martha or Jurídica do: open the shared file, change it, save."""
    path = _excel(container)
    workbook = load_workbook(path)
    edit(workbook.worksheets[0])
    workbook.save(path)


def _row(sheet, filing_number):
    return next(r for r in sheet.iter_rows(min_row=2) if r[0].value == filing_number)


def _values(container, filing_number):
    sheet = load_workbook(_excel(container)).worksheets[0]
    return [c.value for c in _row(sheet, filing_number)]


def test_first_sync_changes_nothing(container):
    state = container.sync_ledger()
    assert state.outcome == SyncOutcome.SYNCED
    assert (state.imported_rows, state.merged_from_excel, state.written_to_excel) == (0, 0, 0)


def test_a_row_typed_by_hand_is_imported_and_numbering_continues(container):
    container.sync_ledger()
    _person_edits(
        container,
        lambda s: s.append(
            [
                "TAC-2026-ER-04818",
                "2026-11-18",
                "Radicado a mano",
                "",
                "Factura",
                "Entregada en ventanilla",
                "VX-1",
                50000,
                "COMPRAS",
                None,
                "Entregado",
                "Radicada por Martha en papel",
            ]
        ),
    )
    container.import_emails(inbox_files(), actor="TEST")
    approved = container.approve_documents(["01.eml__0"], actor="CLERK")
    assert approved[0].filing_number == "TAC-2026-ER-04819"  # no collision with the manual row
    manual = container.ledger_repository.get("TAC-2026-ER-04818")
    assert "MANUAL_ENTRY" in manual.flags and manual.sender == "Radicado a mano"
    assert any(e["event"] == "LEDGER_MANUAL_ROW_IMPORTED" for e in container.list_audit())


def test_legal_closes_a_petition_in_excel_and_it_leaves_the_deadlines(container):
    container.sync_ledger()
    assert any(d.filing_number == "TAC-2026-ER-04792" for d in container.list_deadlines(TODAY))
    _person_edits(
        container, lambda s: setattr(_row(s, "TAC-2026-ER-04792")[10], "value", "Respondido 17-nov")
    )
    state = container.sync_ledger(actor="SYSTEM")
    assert state.merged_from_excel == 1
    assert container.ledger_repository.get("TAC-2026-ER-04792").status == "CLOSED"
    assert all(d.filing_number != "TAC-2026-ER-04792" for d in container.list_deadlines(TODAY))
    assert _values(container, "TAC-2026-ER-04792")[10] == "Respondido 17-nov"  # people's words stay


def test_people_and_docket_edit_the_same_row_without_losing_either(container):
    container.import_emails(inbox_files(), actor="TEST")
    item = container.escalate_hold("05.eml__0", actor="CLERK")
    filing = item.filing_number
    # Martha adds a note by hand; meanwhile the coordinator confirms the fraud in Docket
    _person_edits(
        container,
        lambda s: setattr(_row(s, filing)[11], "value", "Llamaron preguntando por el pago"),
    )
    from app.features.filing.domain.inbox_item import HoldOutcome

    container.verify_hold(
        "05.eml__0", HoldOutcome.REJECTED, "Proveedor confirma fraude", actor="COORDINATOR"
    )
    cells = _values(container, filing)
    assert cells[10] == "Rechazada - fraude confirmado"  # Docket's change
    assert (
        "Llamaron preguntando por el pago" in cells[11] and "NO PAGAR" in cells[11]
    )  # both notes kept


def test_same_cell_changed_on_both_sides_people_win_and_a_conflict_is_recorded(container):
    container.import_emails(inbox_files(), actor="TEST")
    filing = container.escalate_hold("05.eml__0", actor="CLERK").filing_number
    _person_edits(
        container, lambda s: setattr(_row(s, filing)[10], "value", "En revisión con banco")
    )
    from app.features.filing.domain.inbox_item import HoldOutcome

    container.verify_hold(
        "05.eml__0", HoldOutcome.RELEASED, "Confirmado por teléfono", actor="COORDINATOR"
    )
    state = container.sync_ledger.last_state()
    assert state.outcome == SyncOutcome.SYNCED_WITH_CONFLICTS
    assert [(c.filing_number, c.column) for c in state.conflicts] == [(filing, "Estado")]
    assert _values(container, filing)[10] == "En revisión con banco"


def test_a_deleted_row_is_restored(container):
    container.import_emails(inbox_files(), actor="TEST")
    container.approve_documents(["01.eml__0"], actor="CLERK")
    _person_edits(container, lambda s: s.delete_rows(_row(s, "TAC-2026-ER-04818")[0].row))
    state = container.sync_ledger()
    assert (
        state.restored_rows == 1
        and _values(container, "TAC-2026-ER-04818")[0] == "TAC-2026-ER-04818"
    )
    assert any(e["event"] == "LEDGER_ROW_RESTORED" for e in container.list_audit())


def test_an_open_excel_is_never_overwritten(container):
    container.sync_ledger()
    lock = _excel(container).with_name(f"~${_excel(container).name}")
    lock.write_text("abierto por Contabilidad")
    container.import_emails(inbox_files(), actor="TEST")
    approved = container.approve_documents(["01.eml__0"], actor="CLERK")  # approval still works
    assert container.sync_ledger.last_state().outcome == SyncOutcome.LOCKED
    assert all(
        r[0] != approved[0].filing_number
        for r in load_workbook(_excel(container)).worksheets[0].iter_rows(values_only=True)
    )
    lock.unlink()  # Contabilidad closes the file
    assert container.sync_ledger().outcome == SyncOutcome.SYNCED
    assert _values(container, approved[0].filing_number)[0] == approved[0].filing_number


def test_a_save_in_the_middle_of_the_merge_is_merged_again(container, monkeypatch):
    container.import_emails(inbox_files(), actor="TEST")
    real_write = container.workbook.write_table
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise WorkbookChangedError("someone saved")
        return real_write(*args, **kwargs)

    monkeypatch.setattr(container.workbook, "write_table", flaky)
    container.approve_documents(["01.eml__0"], actor="CLERK")
    assert container.sync_ledger.last_state().outcome == SyncOutcome.SYNCED and calls["n"] >= 2
