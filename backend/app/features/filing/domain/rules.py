"""The filing clerk's business rules, as told in the interview.

Pure domain logic: every lookup (supplier master, ledger) is resolved by the application layer
and handed in as `FilingFacts`. Each rule leaves a `Reason` with a stable UPPER_SNAKE_CASE code;
blocking reasons send the document to human review.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.features.catalogs.domain.catalogs import Supplier
from app.features.classification.domain.classifier import Classification
from app.features.classification.domain.text import fold
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.domain.identifiers import email_domain, is_valid_nit, normalize_account
from app.shared.domain.models import (
    Action,
    Decision,
    Department,
    Document,
    DocumentType,
    Evidence,
    ExtractedData,
    Reason,
)

# Legal terms for petitions (Ley 1755 de 2015), in business days
PETITION_TERM_GENERAL = 15
PETITION_TERM_COPIES = 10
PETITION_TERM_CONSULTATION = 30
COMPLAINT_TERM = 15
TRAVEL_REQUEST_MIN_NOTICE = 5  # business days before departure

UNREADABLE_METHODS = {"OCR_UNAVAILABLE", "UNSUPPORTED"}

_CONSULTATION_RE = re.compile(r"\bconcepto\b|\bconsulta\b")
_COPIES_RE = re.compile(r"\bcopias?\b|\bfotocopias?\b|\bcertificad[oa]s?\b|\bcertificacion\b")
_OTHER_REQUESTS_RE = re.compile(
    r"\bse (?:nos |me )?inform[ea]\b|\b(?:me|nos) informen\b|\bindiqu|\bmedidas\b|\breunion\b"
    r"|\bexplicacion\b|\bpaguen?\b|\bsuspend|\bresponda|\bque se (?:nos )?(?:programe|realice)"
)


@dataclass(frozen=True)
class FilingFacts:
    document: Document
    classification: Classification
    data: ExtractedData
    is_ambiguous: bool
    supplier: Supplier | None  # looked up by the NIT in the document
    sender_supplier: Supplier | None  # looked up by the sender's e-mail domain
    existing_filing_number: str | None  # same supplier + invoice number already in the ledger
    pending_duplicate_of: str | None  # same invoice waiting in the inbox (not filed yet)
    body_mentions_account: str  # bank account announced in the e-mail body, if any
    body_announces_account_change: bool
    calendar: BusinessCalendar
    min_ocr_confidence: float

    @property
    def received(self) -> date:
        return self.document.received_at.date()


def _reason(code: str, blocking: bool = False, **params: str) -> Reason:
    return Reason(code=code, blocking=blocking, params={k: str(v) for k, v in params.items()})


def _readability_reasons(facts: FilingFacts) -> list[Reason]:
    doc = facts.document
    if doc.extraction_method in UNREADABLE_METHODS or not doc.text.strip():
        return [_reason("DOCUMENT_UNREADABLE", True, method=doc.extraction_method)]
    if doc.ocr_confidence is not None and doc.ocr_confidence < facts.min_ocr_confidence:
        return [_reason("LOW_OCR_CONFIDENCE", True, confidence=f"{doc.ocr_confidence:.0f}")]
    return []


def _classification_reasons(facts: FilingFacts) -> list[Reason]:
    c = facts.classification
    reasons = []
    if c.document_type == DocumentType.OTHER:
        reasons.append(_reason("UNKNOWN_DOCUMENT_TYPE", True))
    elif facts.is_ambiguous:
        candidates = ",".join(sorted(c.matched))
        reasons.append(_reason("AMBIGUOUS_CLASSIFICATION", True, candidates=candidates))
    if c.source == "LLM":
        reasons.append(_reason("CLASSIFIED_BY_ASSISTANT", True))
    return reasons


# --- Invoices -----------------------------------------------------------------------------


def _decide_invoice(facts: FilingFacts) -> Decision:
    data, supplier = facts.data, facts.supplier
    reasons: list[Reason] = []
    evidence = [
        Evidence(field="nit", value=data.identification, source="ATTACHMENT"),
        Evidence(field="document_number", value=data.document_number, source="ATTACHMENT"),
        Evidence(field="purchase_order", value=data.purchase_order or "-", source="ATTACHMENT"),
        Evidence(field="bank_account", value=data.bank_account or "-", source="ATTACHMENT"),
    ]

    missing = [
        f for f in ("identification", "document_number", "total_amount") if not getattr(data, f)
    ]
    if missing:
        reasons.append(_reason("INVOICE_MISSING_FIELDS", True, fields=",".join(missing)))
    has_totals = data.subtotal and data.tax is not None and data.total_amount
    if has_totals and data.subtotal + data.tax != data.total_amount:
        reasons.append(_reason("INVOICE_TOTALS_MISMATCH", True))

    if supplier is None:
        reasons.append(_reason("SUPPLIER_NOT_REGISTERED", nit=data.identification))
        if data.identification and not is_valid_nit(data.identification):
            # A typo in the NIT would also explain "not registered": worth a look, not a block
            reasons.append(_reason("NIT_CHECK_DIGIT_INVALID", nit=data.identification))
        if not data.purchase_order:
            reasons.append(_reason("INVOICE_WITHOUT_PURCHASE_ORDER"))
        return Decision(
            document_type=DocumentType.INVOICE,
            department=Department.PROCUREMENT,
            action=Action.FILE,
            reasons=reasons,
            evidence=evidence,
        )

    evidence.append(
        Evidence(field="master_account", value=supplier.account_number, source="SUPPLIER_MASTER")
    )
    evidence.append(
        Evidence(field="master_email", value=supplier.billing_email, source="SUPPLIER_MASTER")
    )
    if not supplier.is_active:
        reasons.append(_reason("SUPPLIER_INACTIVE", True, supplier=supplier.name))

    # Fraud guard: account different from the master, or the e-mail comes from a strange address
    fraud: list[Reason] = []
    if data.bank_account and normalize_account(data.bank_account) != normalize_account(
        supplier.account_number
    ):
        fraud.append(
            _reason(
                "INVOICE_ACCOUNT_MISMATCH",
                True,
                invoice=data.bank_account,
                master=supplier.account_number,
            )
        )
    if facts.body_mentions_account and normalize_account(
        facts.body_mentions_account
    ) != normalize_account(supplier.account_number):
        fraud.append(_reason("EMAIL_ACCOUNT_MISMATCH", True, email=facts.body_mentions_account))
    if facts.body_announces_account_change:
        fraud.append(_reason("ACCOUNT_CHANGE_ANNOUNCED", True))
    sender_domain = email_domain(facts.document.sender)
    if sender_domain != supplier.domain:
        fraud.append(
            _reason("SENDER_DOMAIN_MISMATCH", True, sender=sender_domain, master=supplier.domain)
        )
    if fraud:
        return Decision(
            document_type=DocumentType.INVOICE,
            department=Department.ADMIN_COORDINATION,
            action=Action.HOLD_FOR_VERIFICATION,
            reasons=reasons + fraud,
            evidence=evidence,
        )

    if facts.pending_duplicate_of:
        reasons.append(
            _reason("INVOICE_DUPLICATE_IN_INBOX", True, document_id=facts.pending_duplicate_of)
        )

    if facts.existing_filing_number:
        reasons.append(_reason("INVOICE_DUPLICATE", filing_number=facts.existing_filing_number))
        return Decision(
            document_type=DocumentType.INVOICE,
            department=Department.SENDER,
            action=Action.REPLY_WITH_EXISTING_NUMBER,
            existing_filing_number=facts.existing_filing_number,
            reasons=reasons,
            evidence=evidence,
        )

    if data.purchase_order:
        reasons.append(_reason("INVOICE_WITH_PURCHASE_ORDER", purchase_order=data.purchase_order))
        department = Department.ACCOUNTS_PAYABLE
    else:
        reasons.append(_reason("INVOICE_WITHOUT_PURCHASE_ORDER"))
        department = Department.PROCUREMENT
    return Decision(
        document_type=DocumentType.INVOICE,
        department=department,
        action=Action.FILE,
        reasons=reasons,
        evidence=evidence,
    )


# --- Travel expense requests --------------------------------------------------------------


def _decide_travel_request(facts: FilingFacts) -> Decision:
    data = facts.data
    reasons: list[Reason] = []
    if not data.has_official_form:
        reasons.append(_reason("TRAVEL_REQUEST_WITHOUT_FORM"))
    if not (data.approver and data.approver_signed):
        reasons.append(_reason("TRAVEL_REQUEST_NOT_APPROVED"))
    if reasons:
        return Decision(
            document_type=DocumentType.TRAVEL_EXPENSE_REQUEST,
            department=Department.SENDER,
            action=Action.RETURN_TO_SENDER,
            reasons=reasons,
        )

    evidence = [
        Evidence(field="approver", value=data.approver, source="ATTACHMENT"),
        Evidence(
            field="departure_date", value=str(data.departure_date or "-"), source="ATTACHMENT"
        ),
    ]
    late = False
    if data.departure_date is None:
        reasons.append(_reason("TRAVEL_REQUEST_MISSING_DEPARTURE", True))
    elif data.departure_date <= facts.received:
        reasons.append(
            _reason("TRAVEL_REQUEST_DEPARTURE_PASSED", True, departure=str(data.departure_date))
        )
    else:
        notice = facts.calendar.business_days_between(facts.received, data.departure_date)
        if notice < TRAVEL_REQUEST_MIN_NOTICE:
            late = True
            reasons.append(_reason("TRAVEL_REQUEST_LATE", notice_days=str(notice)))
        else:
            reasons.append(_reason("TRAVEL_REQUEST_COMPLETE", notice_days=str(notice)))
    return Decision(
        document_type=DocumentType.TRAVEL_EXPENSE_REQUEST,
        department=Department.HUMAN_RESOURCES,
        action=Action.FILE,
        late=late,
        reasons=reasons,
        evidence=evidence,
    )


# --- Petitions, oversight notices and complaints ------------------------------------------


def petition_scope(text: str) -> str:
    """COPIES_ONLY (10 days), CONSULTATION (30), or GENERAL (15). Copies + other things = 15."""
    folded = fold(text)
    if _CONSULTATION_RE.search(folded):
        return "CONSULTATION"
    if _COPIES_RE.search(folded) and not _OTHER_REQUESTS_RE.search(folded):
        return "COPIES_ONLY"
    return "GENERAL"


def _decide_petition(facts: FilingFacts) -> Decision:
    scope = petition_scope(facts.document.text)
    days = {"COPIES_ONLY": PETITION_TERM_COPIES, "CONSULTATION": PETITION_TERM_CONSULTATION}.get(
        scope, PETITION_TERM_GENERAL
    )
    reasons = [_reason(f"PETITION_{scope}", days=str(days))]
    if "derecho de peticion" not in fold(f"{facts.document.email_subject} {facts.document.text}"):
        reasons.append(_reason("PETITION_IMPLICIT"))
    if facts.data.mentions_tutela:
        reasons.append(_reason("TUTELA_THREAT"))
    holidays = facts.calendar.holidays_in_term(facts.received, days)
    if holidays:
        reasons.append(_reason("HOLIDAY_IN_TERM", holidays=",".join(map(str, holidays))))
    return Decision(
        document_type=DocumentType.PETITION,
        department=Department.LEGAL,
        action=Action.FILE,
        due_date=facts.calendar.add_business_days(facts.received, days),
        urgent=facts.data.mentions_tutela,
        reasons=reasons,
        evidence=[Evidence(field="received_date", value=str(facts.received), source="HEADER")],
    )


def _decide_oversight_notice(facts: FilingFacts) -> Decision:
    data = facts.data
    reasons = [_reason("OVERSIGHT_BODY_URGENT")]
    due: date | None = None
    if data.term_days and data.term_kind == "BUSINESS_DAYS":
        due = facts.calendar.add_business_days(facts.received, data.term_days)
        reasons.append(_reason("TERM_FROM_NOTICE", days=str(data.term_days), kind=data.term_kind))
    elif data.term_days and data.term_kind == "CALENDAR_DAYS":
        due = facts.received + timedelta(days=data.term_days)
        reasons.append(_reason("TERM_FROM_NOTICE", days=str(data.term_days), kind=data.term_kind))
    elif data.term_days:
        reasons.append(_reason("OVERSIGHT_TERM_AMBIGUOUS", True, days=str(data.term_days)))
    else:
        reasons.append(_reason("OVERSIGHT_TERM_NOT_FOUND", True))
    return Decision(
        document_type=DocumentType.OVERSIGHT_NOTICE,
        department=Department.LEGAL,
        action=Action.FILE,
        due_date=due,
        urgent=True,
        reasons=reasons,
        evidence=[
            Evidence(
                field="document_number", value=data.document_number or "-", source="ATTACHMENT"
            )
        ],
    )


def _decide_complaint(facts: FilingFacts) -> Decision:
    reasons = [_reason("COMPLAINT_TERMINAL_USER", days=str(COMPLAINT_TERM))]
    holidays = facts.calendar.holidays_in_term(facts.received, COMPLAINT_TERM)
    if holidays:
        reasons.append(_reason("HOLIDAY_IN_TERM", holidays=",".join(map(str, holidays))))
    if facts.data.mentions_tutela:
        reasons.append(_reason("TUTELA_THREAT"))
    return Decision(
        document_type=DocumentType.COMPLAINT,
        department=Department.CUSTOMER_SERVICE,
        action=Action.FILE,
        due_date=facts.calendar.add_business_days(facts.received, COMPLAINT_TERM),
        urgent=facts.data.mentions_tutela,
        reasons=reasons,
    )


# --- Entry point --------------------------------------------------------------------------


def _decide_by_type(facts: FilingFacts) -> Decision:
    match facts.classification.document_type:
        case DocumentType.INVOICE:
            return _decide_invoice(facts)
        case DocumentType.TRAVEL_EXPENSE_REQUEST:
            return _decide_travel_request(facts)
        case DocumentType.PETITION:
            return _decide_petition(facts)
        case DocumentType.OVERSIGHT_NOTICE:
            return _decide_oversight_notice(facts)
        case DocumentType.COMPLAINT:
            return _decide_complaint(facts)
        case DocumentType.QUOTATION:
            return Decision(
                document_type=DocumentType.QUOTATION,
                department=Department.PROCUREMENT,
                action=Action.FILE,
                reasons=[_reason("QUOTATION_TO_PROCUREMENT")],
            )
        case DocumentType.ADVERTISING:
            return Decision(
                document_type=DocumentType.ADVERTISING,
                department=Department.NONE,
                action=Action.DO_NOT_FILE,
                reasons=[_reason("ADVERTISING_NOT_FILED")],
            )
        case _:
            return Decision(
                document_type=DocumentType.OTHER, department=Department.NONE, action=Action.FILE
            )


def decide(facts: FilingFacts) -> Decision:
    unreadable = _readability_reasons(facts)
    if unreadable:
        return Decision(
            document_type=facts.classification.document_type,
            department=Department.NONE,
            action=Action.FILE,
            reasons=unreadable,
            confidence=0.0,
        )
    decision = _decide_by_type(facts)
    decision.reasons = _classification_reasons(facts) + decision.reasons
    margin_confidence = min(1.0, 0.5 + facts.classification.margin / 10)
    decision.confidence = round(margin_confidence * (0.5 if decision.needs_review else 1.0), 2)
    return decision
