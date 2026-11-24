import pytest

from app.features.classification.domain.classifier import classify
from app.shared.domain.models import DocumentType

EXPECTED = {
    "01.eml": DocumentType.INVOICE,
    "02.eml": DocumentType.INVOICE,
    "04.eml": DocumentType.INVOICE,
    "05.eml": DocumentType.INVOICE,
    "07.eml": DocumentType.TRAVEL_EXPENSE_REQUEST,
    "08.eml": DocumentType.TRAVEL_EXPENSE_REQUEST,
    "10.eml": DocumentType.PETITION,
    "11.eml": DocumentType.OVERSIGHT_NOTICE,
    "12.eml": DocumentType.PETITION,
    "13.eml": DocumentType.QUOTATION,
    "14.eml": DocumentType.COMPLAINT,
    "15.eml": DocumentType.ADVERTISING,
}


@pytest.mark.parametrize("email_file,expected", EXPECTED.items())
def test_mailbox_documents_are_classified(email_file, expected, documents_by_email):
    doc = documents_by_email[email_file][0]
    result = classify(doc.text, doc.email_subject)
    assert result.document_type == expected
    assert result.margin >= 2  # clear decisions, not guesses


def test_implicit_petition_without_the_words_derecho_de_peticion():
    result = classify(
        "Buenos días, les pido que me informen el horario de atención del patio de contenedores"
    )
    assert result.document_type == DocumentType.PETITION


def test_empty_text_is_other():
    assert classify("").document_type == DocumentType.OTHER
