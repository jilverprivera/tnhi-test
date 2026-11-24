from openpyxl import load_workbook

from app.features.ledger.domain.filing_number import format_filing_number, parse_sequence
from app.shared.config import MATERIAL
from app.shared.domain.models import Department, DocumentType, LedgerStatus

ORIGINAL = MATERIAL / "3-datos-del-cliente" / "libro-radicacion-2026.xlsx"


def test_filing_number_format():
    assert format_filing_number("TAC-2026-ER-", 4818) == "TAC-2026-ER-04818"
    assert parse_sequence("TAC-2026-ER-04817", "TAC-2026-ER-") == 4817
    assert parse_sequence("OTRO-1", "TAC-2026-ER-") is None


def test_ledger_is_seeded_from_the_client_excel(container):
    entries = container.ledger_repository.all_entries()
    assert len(entries) == 28 and container.ledger_repository.last_sequence() == 4817
    first = entries[0]
    assert (first.document_type, first.department, first.status) == (
        DocumentType.INVOICE,
        Department.ACCOUNTS_PAYABLE,
        LedgerStatus.DELIVERED,
    )


def test_duplicate_lookup_is_by_supplier_and_number(container):
    repo = container.ledger_repository
    assert repo.find_invoice("860.555.444-3", "fe-1207") == "TAC-2026-ER-04790"
    assert repo.find_invoice("901.234.567-1", "FE-1207") is None  # same number, other supplier


def test_historical_duplicates_are_reported(container):
    groups = container.find_ledger_duplicates()
    assert ["TAC-2026-ER-04809", "TAC-2026-ER-04813"] in groups


def test_export_keeps_original_rows_and_columns(container):
    from tests.conftest import inbox_files

    container.import_emails(inbox_files(), actor="TEST")
    container.approve_documents(["01.eml__0", "11.eml__0"], actor="CLERK")
    sheet = load_workbook(container.settings.data_dir / "libro-radicacion-2026.xlsx").worksheets[0]
    original = load_workbook(ORIGINAL).worksheets[0]
    for r in range(1, original.max_row + 1):
        assert [c.value for c in sheet[r]] == [c.value for c in original[r]]
    new_rows = list(sheet.iter_rows(min_row=original.max_row + 1, values_only=True))
    assert [r[0] for r in new_rows] == ["TAC-2026-ER-04818", "TAC-2026-ER-04819"]
    oficio = new_rows[1]
    assert (
        oficio[4] == "Oficio ente de control"
        and oficio[8] == "JURIDICA"
        and oficio[9] == "2026-11-23"
    )
    assert oficio[11].startswith("URGENTE")


def test_original_material_is_never_modified(container):
    before = ORIGINAL.read_bytes()
    container.export_ledger()
    assert ORIGINAL.read_bytes() == before
