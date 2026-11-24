"""Golden tests: the mailbox must end up as the client said (and as we decided for the rest)."""

import csv
from datetime import date
from pathlib import Path

import pytest

from app.features.filing.application.correct_document import Correction
from app.shared.config import MATERIAL
from app.shared.domain.models import Action, Department, DocumentStatus
from app.shared.infrastructure.client_vocabulary import (
    CLIENT_CODE_TO_DEPARTMENT,
    CLIENT_LABEL_TO_DOCUMENT_TYPE,
)
from tests.conftest import OCR_AVAILABLE, inbox_files

PARTIAL = MATERIAL / "4-para-medirte" / "esperado-parcial.csv"
FULL = Path(__file__).parent / "esperado-completo.csv"
CLIENT_ACTIONS = {
    "Radicar": Action.FILE,
    "Devolver": Action.RETURN_TO_SENDER,
    "No radicar": Action.DO_NOT_FILE,
}


def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _item_for(container, email_file: str, document: str):
    for item in container.list_inbox():
        doc = item.proposal.document
        if doc.email_file == email_file and (
            doc.name == document or document.startswith("(cuerpo")
        ):
            return item
    raise AssertionError(f"{email_file}/{document} not found")


@pytest.mark.parametrize("row", _rows(PARTIAL), ids=lambda r: r["correo"])
def test_matches_the_clients_expected_results(row, imported_container):
    item = _item_for(imported_container, row["correo"], row["documento"])
    d = item.decision
    assert d.document_type == CLIENT_LABEL_TO_DOCUMENT_TYPE[row["tipo"]]
    assert d.department == CLIENT_CODE_TO_DEPARTMENT[row["dependencia"]]
    assert d.action == CLIENT_ACTIONS[row["accion"]]
    assert d.due_date == (date.fromisoformat(row["vence"]) if row["vence"] else None)


@pytest.mark.parametrize("row", _rows(FULL), ids=lambda r: f"{r['correo']}-{r['documento']}")
def test_matches_the_full_expected_table(row, imported_container):
    item = _item_for(imported_container, row["correo"], row["documento"])
    if row["correo"] == "03.eml" and not OCR_AVAILABLE:
        # Without OCR the scan cannot be read: it must go to a person, never be guessed
        assert item.status == DocumentStatus.NEEDS_REVIEW
        assert item.decision.reason_codes() == ["DOCUMENT_UNREADABLE"]
        return
    d = item.decision
    assert (d.document_type, d.department, d.action) == (
        row["tipo"],
        row["dependencia"],
        row["accion"],
    )
    assert d.due_date == (date.fromisoformat(row["vence"]) if row["vence"] else None)


def test_filing_numbers_continue_the_ledger(container):
    """Approve everything as proposed (fixing the unreadable scan by hand) -> 04818..04831."""
    container.import_emails(inbox_files(), actor="TEST")
    if not OCR_AVAILABLE:
        container.correct_document(
            "03.eml__0",
            Correction(
                document_type="INVOICE", department=Department.ACCOUNTS_PAYABLE, action=Action.FILE
            ),
            actor="CLERK",
        )
    container.approve_documents(
        [i.id for i in container.list_inbox()], actor="CLERK", escalate_holds=True
    )
    expected = {f"{r['correo']}#{r['documento']}": r["radicado"] or None for r in _rows(FULL)}
    actual = {
        f"{i.proposal.document.email_file}#{i.proposal.document.name}": i.filing_number
        for i in container.list_inbox()
    }
    assert actual == expected
