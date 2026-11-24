from datetime import date

from app.features.classification.domain.field_extractor import (
    announces_account_change,
    bank_accounts,
    extract_for,
    extract_term,
)
from app.shared.domain.models import DocumentType

TAC = "900.100.200-3"


def test_invoice_fields(documents_by_email):
    data = extract_for(DocumentType.INVOICE, documents_by_email["01.eml"][0].text, TAC)
    assert data.identification == "901.234.567-1"  # not TAC's own NIT
    assert data.document_number == "FE-3381"
    assert data.purchase_order == "OC-2026-0412"
    assert data.bank_account == "123-45678-9"
    assert (data.subtotal, data.tax, data.total_amount) == (4_600_000, 874_000, 5_474_000)
    assert data.issue_date == date(2026, 11, 9)


def test_invoice_without_purchase_order(documents_by_email):
    data = extract_for(DocumentType.INVOICE, documents_by_email["02.eml"][0].text, TAC)
    assert data.purchase_order == ""


def test_travel_request_fields(documents_by_email):
    data = extract_for(
        DocumentType.TRAVEL_EXPENSE_REQUEST, documents_by_email["09.eml"][0].text, TAC
    )
    assert data.has_official_form and data.approver_signed
    assert data.departure_date == date(2026, 11, 19)
    assert data.total_amount == 840_000


def test_term_written_in_words_and_digits():
    assert extract_term("dentro de los cinco (5) días hábiles siguientes") == (5, "BUSINESS_DAYS")
    assert extract_term("en un plazo de diez días calendario") == (10, "CALENDAR_DAYS")
    assert extract_term("sin plazo") == (None, "")


def test_account_change_announced_in_body(documents_by_email):
    body = documents_by_email["05.eml"][0].email_body
    assert announces_account_change(body)
    assert bank_accounts(body)[0][1] == "912-345678-90"
