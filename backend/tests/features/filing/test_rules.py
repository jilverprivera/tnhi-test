"""One test per business rule from the interview, on synthetic facts."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.features.catalogs.domain.catalogs import Supplier
from app.features.classification.domain.classifier import Classification
from app.features.filing.domain.rules import FilingFacts, decide, petition_scope
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.domain.models import Action, Department, Document, DocumentType, ExtractedData

BOGOTA = ZoneInfo("America/Bogota")
SUPPLIER = Supplier(
    nit="901.234.567-1",
    name="Suministros",
    billing_email="facturacion@suministrosllano.example",
    bank="Banco de Bogotá",
    account_type="Corriente",
    account_number="123-45678-9",
    status="ACTIVO",
    category="EPP",
)


def facts(
    doc_type=DocumentType.INVOICE,
    text="texto",
    sender="facturacion@suministrosllano.example",
    received=date(2026, 11, 17),
    data=None,
    **overrides,
) -> FilingFacts:
    document = Document(
        email_file="t.eml",
        position=0,
        name="doc.pdf",
        text=text,
        extraction_method="PDF_TEXT",
        received_at=datetime(received.year, received.month, received.day, 9, tzinfo=BOGOTA),
        sender=sender,
        sender_name="Remitente",
        email_subject="asunto",
    )
    base = {
        "document": document,
        "classification": Classification(doc_type, 9, 9),
        "data": data or ExtractedData(),
        "is_ambiguous": False,
        "supplier": None,
        "sender_supplier": None,
        "existing_filing_number": None,
        "pending_duplicate_of": None,
        "body_mentions_account": "",
        "body_announces_account_change": False,
        "calendar": BusinessCalendar(),
        "min_ocr_confidence": 70,
    }
    return FilingFacts(**(base | overrides))


def invoice(**kw) -> ExtractedData:
    values = {
        "identification": "901.234.567-1",
        "document_number": "FE-1",
        "total_amount": 119,
        "subtotal": 100,
        "tax": 19,
        "purchase_order": "OC-2026-0001",
        "bank_account": "123-45678-9",
    }
    return ExtractedData(**(values | kw))


# --- invoices --------------------------------------------------------------------------


def test_registered_supplier_with_purchase_order_goes_to_accounts_payable():
    d = decide(facts(data=invoice(), supplier=SUPPLIER))
    assert (d.department, d.action, d.needs_review) == (
        Department.ACCOUNTS_PAYABLE,
        Action.FILE,
        False,
    )


def test_registered_supplier_without_purchase_order_goes_to_procurement():
    d = decide(facts(data=invoice(purchase_order=""), supplier=SUPPLIER))
    assert (
        d.department == Department.PROCUREMENT
        and "INVOICE_WITHOUT_PURCHASE_ORDER" in d.reason_codes()
    )


def test_unregistered_supplier_goes_to_procurement_to_be_linked():
    d = decide(facts(data=invoice(), supplier=None))
    assert d.department == Department.PROCUREMENT and "SUPPLIER_NOT_REGISTERED" in d.reason_codes()


def test_duplicate_invoice_is_not_filed_again():
    d = decide(facts(data=invoice(), supplier=SUPPLIER, existing_filing_number="TAC-2026-ER-04790"))
    assert (
        d.action == Action.REPLY_WITH_EXISTING_NUMBER
        and d.existing_filing_number == "TAC-2026-ER-04790"
    )


def test_account_different_from_master_is_held_for_the_coordinator():
    d = decide(facts(data=invoice(bank_account="999-999999-99"), supplier=SUPPLIER))
    assert (d.department, d.action) == (Department.ADMIN_COORDINATION, Action.HOLD_FOR_VERIFICATION)
    assert d.needs_review and "INVOICE_ACCOUNT_MISMATCH" in d.reason_codes()


def test_strange_sender_address_is_held_even_if_account_matches():
    d = decide(
        facts(data=invoice(), supplier=SUPPLIER, sender="facturacion@suministros-llano.example")
    )
    assert d.action == Action.HOLD_FOR_VERIFICATION and "SENDER_DOMAIN_MISMATCH" in d.reason_codes()


def test_fraud_check_wins_over_duplicate():
    d = decide(
        facts(data=invoice(bank_account="1"), supplier=SUPPLIER, existing_filing_number="TAC-1")
    )
    assert d.action == Action.HOLD_FOR_VERIFICATION


def test_inactive_supplier_needs_review():
    inactive = Supplier(**{**SUPPLIER.__dict__, "status": "INACTIVO"})
    assert "SUPPLIER_INACTIVE" in decide(facts(data=invoice(), supplier=inactive)).reason_codes()


def test_totals_that_do_not_add_up_need_review():
    d = decide(facts(data=invoice(total_amount=500), supplier=SUPPLIER))
    assert d.needs_review and "INVOICE_TOTALS_MISMATCH" in d.reason_codes()


def test_missing_invoice_fields_need_review():
    d = decide(facts(data=invoice(document_number=""), supplier=SUPPLIER))
    assert d.needs_review and "INVOICE_MISSING_FIELDS" in d.reason_codes()


# --- travel expense requests ------------------------------------------------------------


def travel(**kw) -> ExtractedData:
    values = {
        "has_official_form": True,
        "approver": "Jefe",
        "approver_signed": True,
        "departure_date": date(2026, 11, 30),
    }
    return ExtractedData(**(values | kw))


def test_travel_request_on_time_goes_to_human_resources():
    d = decide(facts(DocumentType.TRAVEL_EXPENSE_REQUEST, data=travel()))
    assert (d.department, d.late) == (Department.HUMAN_RESOURCES, False)


def test_late_travel_request_is_still_filed_but_flagged():
    d = decide(
        facts(DocumentType.TRAVEL_EXPENSE_REQUEST, data=travel(departure_date=date(2026, 11, 19)))
    )
    assert (
        d.department == Department.HUMAN_RESOURCES
        and d.late
        and "TRAVEL_REQUEST_LATE" in d.reason_codes()
    )


def test_travel_request_without_approval_is_returned():
    d = decide(facts(DocumentType.TRAVEL_EXPENSE_REQUEST, data=travel(approver_signed=False)))
    assert d.action == Action.RETURN_TO_SENDER and "TRAVEL_REQUEST_NOT_APPROVED" in d.reason_codes()


def test_travel_request_outside_the_form_is_returned():
    d = decide(facts(DocumentType.TRAVEL_EXPENSE_REQUEST, data=travel(has_official_form=False)))
    assert d.action == Action.RETURN_TO_SENDER and "TRAVEL_REQUEST_WITHOUT_FORM" in d.reason_codes()


# --- petitions, notices, complaints -----------------------------------------------------


def test_petition_scope_rules():
    assert (
        petition_scope("solicito copia del contrato y de los informes de supervisión")
        == "COPIES_ONLY"
    )
    assert (
        petition_scope("solicito copia del contrato y que se nos informe qué medidas tomarán")
        == "GENERAL"
    )
    assert petition_scope("solicito un concepto sobre la norma aplicable") == "CONSULTATION"
    assert petition_scope("solicito que se programe una reunión") == "GENERAL"


def test_petition_terms_15_10_30_business_days():
    received = date(2026, 11, 10)
    general = decide(facts(DocumentType.PETITION, text="solicito una reunión", received=received))
    copies = decide(
        facts(DocumentType.PETITION, text="solicito copias del contrato", received=received)
    )
    consult = decide(facts(DocumentType.PETITION, text="solicito concepto", received=received))
    assert general.due_date == date(2026, 12, 2)
    assert copies.due_date == BusinessCalendar().add_business_days(received, 10)
    assert consult.due_date == BusinessCalendar().add_business_days(received, 30)
    assert general.department == Department.LEGAL


def test_tutela_threat_makes_it_urgent():
    d = decide(
        facts(
            DocumentType.PETITION,
            text="si no responden pondré una tutela",
            data=ExtractedData(mentions_tutela=True),
        )
    )
    assert d.urgent and "TUTELA_THREAT" in d.reason_codes()


def test_oversight_notice_uses_the_term_in_the_notice_and_is_urgent():
    d = decide(
        facts(
            DocumentType.OVERSIGHT_NOTICE,
            received=date(2026, 11, 13),
            data=ExtractedData(term_days=5, term_kind="BUSINESS_DAYS"),
        )
    )
    assert d.urgent and d.department == Department.LEGAL and d.due_date == date(2026, 11, 23)


def test_oversight_notice_without_a_readable_term_needs_review():
    d = decide(facts(DocumentType.OVERSIGHT_NOTICE, data=ExtractedData()))
    assert d.urgent and d.needs_review and "OVERSIGHT_TERM_NOT_FOUND" in d.reason_codes()


def test_complaint_goes_to_customer_service_with_15_business_days():
    d = decide(facts(DocumentType.COMPLAINT, received=date(2026, 11, 17)))
    assert d.department == Department.CUSTOMER_SERVICE and d.due_date == date(2026, 12, 9)


def test_quotation_and_advertising():
    assert decide(facts(DocumentType.QUOTATION)).department == Department.PROCUREMENT
    assert decide(facts(DocumentType.ADVERTISING)).action == Action.DO_NOT_FILE


# --- knows when it does not know --------------------------------------------------------


def test_unreadable_document_needs_review():
    f = facts(text="")
    d = decide(f)
    assert d.needs_review and d.reason_codes() == ["DOCUMENT_UNREADABLE"]


def test_low_ocr_confidence_needs_review():
    f = facts(data=invoice(), supplier=SUPPLIER)
    f.document.ocr_confidence = 40.0
    assert "LOW_OCR_CONFIDENCE" in decide(f).reason_codes()


def test_ambiguous_classification_needs_review():
    d = decide(facts(DocumentType.COMPLAINT, is_ambiguous=True))
    assert d.needs_review and "AMBIGUOUS_CLASSIFICATION" in d.reason_codes()


def test_unknown_type_needs_review():
    assert decide(facts(DocumentType.OTHER)).needs_review
