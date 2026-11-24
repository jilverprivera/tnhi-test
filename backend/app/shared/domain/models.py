"""Shared domain model for document filing.

Enumerated values are UPPER_SNAKE_CASE English codes; translation to Spanish happens only
at the edges (UI labels and the client's Excel ledger).
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    INVOICE = "INVOICE"
    TRAVEL_EXPENSE_REQUEST = "TRAVEL_EXPENSE_REQUEST"
    PETITION = "PETITION"
    OVERSIGHT_NOTICE = "OVERSIGHT_NOTICE"  # control bodies or courts
    COMPLAINT = "COMPLAINT"
    QUOTATION = "QUOTATION"
    ADVERTISING = "ADVERTISING"
    OTHER = "OTHER"


class Department(StrEnum):
    ACCOUNTS_PAYABLE = "ACCOUNTS_PAYABLE"
    PROCUREMENT = "PROCUREMENT"
    HUMAN_RESOURCES = "HUMAN_RESOURCES"
    LEGAL = "LEGAL"
    CUSTOMER_SERVICE = "CUSTOMER_SERVICE"
    ADMIN_COORDINATION = "ADMIN_COORDINATION"  # fraud verification by the coordinator
    SENDER = "SENDER"  # returned to whoever sent it
    NONE = "NONE"  # not filed


class Action(StrEnum):
    FILE = "FILE"
    RETURN_TO_SENDER = "RETURN_TO_SENDER"
    DO_NOT_FILE = "DO_NOT_FILE"
    REPLY_WITH_EXISTING_NUMBER = "REPLY_WITH_EXISTING_NUMBER"
    HOLD_FOR_VERIFICATION = "HOLD_FOR_VERIFICATION"


class DocumentStatus(StrEnum):
    READY = "READY"  # the proposal is safe; the clerk only confirms
    NEEDS_REVIEW = "NEEDS_REVIEW"  # the system is not sure: a person decides
    APPROVED = "APPROVED"
    DISCARDED = "DISCARDED"


class Evidence(BaseModel):
    """Fragment that backs a decision."""

    field: str
    value: str
    source: str  # "ATTACHMENT", "BODY", "HEADER", "SUPPLIER_MASTER", "LEDGER"


class Reason(BaseModel):
    """Why the system decided something. `code` is stable; the UI translates it."""

    code: str
    params: dict[str, str] = Field(default_factory=dict)
    blocking: bool = False  # True => requires human review


class Decision(BaseModel):
    document_type: DocumentType
    department: Department
    action: Action
    due_date: date | None = None
    urgent: bool = False
    late: bool = False  # travel request filed with less notice than required
    reasons: list[Reason] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = 1.0
    existing_filing_number: str | None = None  # for duplicates

    @property
    def needs_review(self) -> bool:
        return any(r.blocking for r in self.reasons)

    @property
    def is_fileable(self) -> bool:
        return self.action in (Action.FILE, Action.HOLD_FOR_VERIFICATION)

    def reason_codes(self) -> list[str]:
        return [r.code for r in self.reasons]


class ExtractedData(BaseModel):
    """The fields that matter, depending on the document type."""

    sender_name: str = ""
    identification: str = ""  # NIT, national ID or e-mail
    document_number: str = ""
    subject: str = ""
    total_amount: int | None = None
    subtotal: int | None = None
    tax: int | None = None
    purchase_order: str = ""
    bank_account: str = ""
    bank: str = ""
    issue_date: date | None = None
    # travel expense requests
    departure_date: date | None = None
    approver: str = ""
    approver_signed: bool = False
    has_official_form: bool = False
    # petitions / oversight notices
    term_days: int | None = None
    term_kind: str = ""  # "BUSINESS_DAYS" | "CALENDAR_DAYS"
    mentions_tutela: bool = False


class Document(BaseModel):
    """A fileable unit: an attachment or the e-mail body."""

    email_file: str
    position: int  # order inside the e-mail
    name: str  # attachment file name or BODY_DOCUMENT_NAME
    text: str
    extraction_method: str  # "PDF_TEXT", "OCR", "EMAIL_BODY", "DOCX", ...
    ocr_confidence: float | None = None
    received_at: datetime
    sender: str
    sender_name: str
    email_subject: str
    email_body: str = ""  # context, e.g. an account change announced in the body

    @property
    def id(self) -> str:
        return f"{self.email_file}__{self.position}"


class Proposal(BaseModel):
    document: Document
    data: ExtractedData
    decision: Decision

    @property
    def status(self) -> DocumentStatus:
        return DocumentStatus.NEEDS_REVIEW if self.decision.needs_review else DocumentStatus.READY


class LedgerStatus(StrEnum):
    DELIVERED = "DELIVERED"  # forwarded to the department
    IN_PROGRESS = "IN_PROGRESS"  # has a legal term running
    ON_HOLD = "ON_HOLD"  # held for verification with the supplier


class LedgerEntry(BaseModel):
    """One row of the filing ledger (same 12 columns as the client's Excel)."""

    filing_number: str
    received_date: date
    sender: str
    identification: str
    document_type: DocumentType
    subject: str
    document_number: str
    total_amount: int | None = None
    department: Department
    due_date: date | None = None
    status: LedgerStatus
    notes: str = ""  # free text written by people (historical rows keep theirs)
    flags: list[str] = Field(default_factory=list)  # reason codes worth showing in the ledger
    urgent: bool = False
    source_document_id: str | None = None  # None for rows imported from the historical Excel
