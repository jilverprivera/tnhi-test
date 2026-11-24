"""Retention (Ley 594 de 2000): nothing is destroyed early, content goes away, the index stays."""

from datetime import date

import pytest
from openpyxl import load_workbook

from app.features.records.application.use_cases import (
    DispositionNotAllowedError,
    RetentionNotExpiredError,
)
from app.features.records.domain.retention import DEFAULT_SCHEDULE, RetentionStatus, retention_ends
from app.shared.domain.models import DocumentType
from app.shared.domain.pagination import PageRequest
from tests.conftest import inbox_files

ALL = PageRequest(limit=200)


@pytest.fixture
def filed(container):
    container.import_emails(inbox_files(), actor="TEST")
    container.approve_documents(["01.eml__0", "11.eml__0", "13.eml__0"], actor="CLERK")
    return container


def test_accounting_support_is_kept_ten_years_from_year_end(filed):
    invoice = filed.ledger_repository.get("TAC-2026-ER-04818")
    assert retention_ends(invoice, DEFAULT_SCHEDULE[DocumentType.INVOICE]) == date(2036, 12, 31)


def test_nothing_is_due_today(filed):
    due = filed.list_retention(date(2026, 11, 18), RetentionStatus.DUE_FOR_DISPOSITION, ALL)
    assert due.total == 0


def test_dispose_removes_content_and_keeps_the_index(filed):
    later = date(2037, 1, 2)
    due = {
        v.filing_number
        for v in filed.list_retention(later, RetentionStatus.DUE_FOR_DISPOSITION, ALL).items
    }
    assert "TAC-2026-ER-04818" in due
    view = filed.dispose_record("TAC-2026-ER-04818", "Acta 07-2037", later, actor="COORDINATOR")
    assert view.status == RetentionStatus.DISPOSED
    item = filed.get_inbox_item("01.eml__0")
    assert (
        item.proposal.document.text == ""
        and filed.inbox_repository.source_file("01.eml__0") is None
    )
    assert item.filing_number == "TAC-2026-ER-04818"  # the decision and the index survive
    sheet = load_workbook(filed.settings.data_dir / "libro-radicacion-2026.xlsx").worksheets[0]
    row = next(r for r in sheet.iter_rows(values_only=True) if r[0] == "TAC-2026-ER-04818")
    assert "Eliminado según la Tabla de Retención Documental" in row[11]
    assert any(e["event"] == "RECORD_DISPOSED" for e in filed.list_audit("01.eml__0"))


def test_never_before_the_term_and_never_what_must_be_conserved(filed):
    with pytest.raises(RetentionNotExpiredError):
        filed.dispose_record("TAC-2026-ER-04818", "Acta 01", date(2030, 1, 1), actor="COORDINATOR")
    oversight = filed.get_inbox_item(
        "11.eml__0"
    ).filing_number  # Contraloría notice: total conservation
    with pytest.raises(DispositionNotAllowedError):
        filed.dispose_record(oversight, "Acta 01", date(2060, 1, 1), actor="COORDINATOR")


def test_historical_rows_are_covered_too(filed):
    page = filed.list_retention(date(2026, 11, 18), None, ALL)
    assert page.total == 31  # 28 historical + 3 filed now
