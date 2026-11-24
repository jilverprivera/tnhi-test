import pytest

from app.features.filing.application.approve_documents import (
    DecisionIncompleteError,
    DocumentNotApprovableError,
)
from app.features.filing.application.correct_document import Correction, DocumentAlreadyClosedError
from app.shared.domain.models import Action, Department, DocumentStatus
from tests.conftest import inbox_files


@pytest.fixture
def loaded(container):
    container.import_emails(inbox_files(), actor="TEST")
    return container


def test_import_is_idempotent(loaded):
    again = loaded.import_emails(inbox_files(), actor="TEST")
    assert again.imported == [] and len(again.skipped) == 17


def test_filing_numbers_are_assigned_on_approval_in_reception_order(loaded):
    ids = ["16.eml__1", "01.eml__0", "16.eml__0"]  # deliberately unordered
    approved = loaded.approve_documents(ids, actor="CLERK")
    assert [(i.id, i.filing_number) for i in approved] == [
        ("01.eml__0", "TAC-2026-ER-04818"),
        ("16.eml__0", "TAC-2026-ER-04819"),
        ("16.eml__1", "TAC-2026-ER-04820"),
    ]


def test_batch_approval_only_takes_ready_documents(loaded):
    approved = loaded.approve_ready(actor="CLERK")
    statuses = {i.id: i.status for i in loaded.list_inbox()}
    assert approved and all(statuses[i.id] == DocumentStatus.APPROVED for i in approved)
    assert (
        statuses["05.eml__0"] == DocumentStatus.NEEDS_REVIEW
    )  # possible fraud is never batch-approved


def test_ready_only_approval_rejects_documents_that_need_review(loaded):
    with pytest.raises(DocumentNotApprovableError):
        loaded.approve_documents(["05.eml__0"], actor="CLERK", allow_review=False)


def test_unreadable_document_cannot_be_filed_without_a_department(loaded):
    item = loaded.get_inbox_item("03.eml__0")
    if item.decision.department != Department.NONE:
        pytest.skip("OCR available: the scanned invoice was read")
    with pytest.raises(DecisionIncompleteError):
        loaded.approve_documents(["03.eml__0"], actor="CLERK")


def test_correction_keeps_the_original_proposal_and_is_audited(loaded):
    original = loaded.get_inbox_item("03.eml__0").proposal.decision
    item = loaded.correct_document(
        "03.eml__0",
        Correction(
            department=Department.ACCOUNTS_PAYABLE,
            action=Action.FILE,
            notes="Leída a mano: SE-77821",
        ),
        actor="CLERK",
    )
    assert item.status == DocumentStatus.READY and item.was_corrected
    assert item.proposal.decision == original  # what the system proposed is never overwritten
    assert "REVIEWED_BY_HUMAN" in item.decision.reason_codes()
    assert any(e["event"] == "DOCUMENT_CORRECTED" for e in loaded.list_audit("03.eml__0"))
    approved = loaded.approve_documents(["03.eml__0"], actor="CLERK")
    assert approved[0].filing_number == "TAC-2026-ER-04818"


def test_approved_documents_cannot_be_corrected(loaded):
    loaded.approve_documents(["01.eml__0"], actor="CLERK")
    with pytest.raises(DocumentAlreadyClosedError):
        loaded.correct_document("01.eml__0", Correction(urgent=True), actor="CLERK")


def test_approval_writes_simulated_outbox_messages(loaded):
    loaded.approve_documents(["01.eml__0", "05.eml__0", "06.eml__0", "08.eml__0"], actor="CLERK")
    kinds = {m.document_id: m.kind for m in loaded.list_outbox()}
    assert kinds == {
        "01.eml__0": "FORWARD_TO_DEPARTMENT",
        "05.eml__0": "FRAUD_ALERT",
        "06.eml__0": "REPLY_EXISTING_NUMBER",
        "08.eml__0": "RETURN_TO_SENDER",
    }
    reply = next(m for m in loaded.list_outbox() if m.document_id == "06.eml__0")
    assert "TAC-2026-ER-04790" in reply.body


def test_duplicate_inside_the_same_batch_needs_review(container):
    files = dict(inbox_files())
    container.import_emails(
        [("01.eml", files["01.eml"]), ("01-copy.eml", files["01.eml"])], actor="TEST"
    )
    copy = container.get_inbox_item("01-copy.eml__0")
    assert (
        "INVOICE_DUPLICATE_IN_INBOX" in copy.decision.reason_codes() and copy.decision.needs_review
    )
