"""Field extraction with regular expressions and validators, per document type."""

import re
from datetime import date

from app.features.classification.domain.text import SPANISH_NUMBER_WORDS, fold, parse_amount
from app.shared.domain.identifiers import normalize_nit
from app.shared.domain.models import DocumentType, ExtractedData

NIT_RE = re.compile(r"NIT\.?\s*:?\s*(\d{1,3}(?:\.\d{3}){2}-\d|\d{8,10}-\d)", re.IGNORECASE)
INVOICE_NUMBER_RE = re.compile(r"\bNo\.?\s*:?\s*([A-Z]{1,5}(?:-\d{4})?-\d{2,7})\b")
PURCHASE_ORDER_RE = re.compile(r"\b(OC-\d{4}-\d{3,5})\b", re.IGNORECASE)
ACCOUNT_RE = re.compile(
    r"(?P<bank>Banco [A-ZÁÉÍÓÚa-záéíóúñ ]+?|Bancolombia|Davivienda|BBVA)?,?\s*"
    r"cuenta\s+(?:de\s+)?(?:corriente|ahorros)?\s*(?:(?:Bancolombia|Davivienda|BBVA|Banco\s+\w+)\s*)?"
    r"(?:No\.?|número|#)\s*(?P<number>[\d][\d-]{5,})",
    re.IGNORECASE,
)
TOTAL_RE = re.compile(r"(?<![a-z])TOTAL(?:\s+A\s+PAGAR)?\s*:?\s*\$\s*([\d.,]+)", re.IGNORECASE)
SUBTOTAL_RE = re.compile(r"Subtotal\s*\$\s*([\d.,]+)", re.IGNORECASE)
TAX_RE = re.compile(r"IVA[^$\n]*\$\s*([\d.,]+)", re.IGNORECASE)
ISO_DATE_RE = re.compile(r"Fecha(?: de expedición)?\s*:?\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
DMY = r"(\d{1,2})/(\d{1,2})/(\d{4})"
OFFICIAL_NUMBER_RE = re.compile(
    r"(?:Oficio|COTIZACI[ÓO]N)\s*(?:No\.?)?\s*([A-Z]{2,4}-\d{4}-\d{3,5})", re.IGNORECASE
)
TERM_RE = re.compile(
    r"(?:dentro de (?:los )?|plazo de |termino de )?"
    r"(?:(?P<word>[a-z]+)\s*)?\(?(?P<num>\d{1,3})?\)?\s*dias\s*(?P<kind>habiles|calendario)?",
)
ACCOUNT_CHANGE_RE = re.compile(
    r"cambi\w*\s+(?:de\s+|nuestra\s+|la\s+)?cuenta|nueva cuenta|actualizar sus datos"
)
TUTELA_RE = re.compile(r"\btutela\b")


def _first(regex: re.Pattern, text: str) -> str:
    match = regex.search(text)
    return match.group(1) if match else ""


def _dmy_after(label: str, text: str) -> date | None:
    match = re.search(label + r"\s*:?\s*" + DMY, text, re.IGNORECASE)
    if not match:
        return None
    day, month, year = (int(g) for g in match.groups())
    return date(year, month, day)


def supplier_nit(text: str, company_nit: str) -> str:
    """First NIT in the document that is not TAC's own NIT."""
    own = normalize_nit(company_nit)
    return next((n for n in NIT_RE.findall(text) if normalize_nit(n) != own), "")


def bank_accounts(text: str) -> list[tuple[str, str]]:
    return [
        ((m.group("bank") or "").strip(), m.group("number").strip("-"))
        for m in ACCOUNT_RE.finditer(text)
    ]


def announces_account_change(text: str) -> bool:
    return bool(ACCOUNT_CHANGE_RE.search(fold(text)))


def extract_term(text: str) -> tuple[int | None, str]:
    """Term written in a notice, e.g. 'cinco (5) días hábiles' -> (5, 'BUSINESS_DAYS')."""
    for match in TERM_RE.finditer(fold(text)):
        days = (
            int(match.group("num"))
            if match.group("num")
            else SPANISH_NUMBER_WORDS.get(match.group("word") or "")
        )
        if not days:
            continue
        kind = {"habiles": "BUSINESS_DAYS", "calendario": "CALENDAR_DAYS"}.get(
            match.group("kind") or "", ""
        )
        return days, kind
    return None, ""


def extract_invoice(text: str, company_nit: str) -> ExtractedData:
    accounts = bank_accounts(text)
    issue = _first(ISO_DATE_RE, text)
    return ExtractedData(
        identification=supplier_nit(text, company_nit),
        document_number=_first(INVOICE_NUMBER_RE, text),
        purchase_order=_first(PURCHASE_ORDER_RE, text).upper(),
        bank=accounts[0][0] if accounts else "",
        bank_account=accounts[0][1] if accounts else "",
        total_amount=parse_amount(_first(TOTAL_RE, text)),
        subtotal=parse_amount(_first(SUBTOTAL_RE, text)),
        tax=parse_amount(_first(TAX_RE, text)),
        issue_date=date.fromisoformat(issue) if issue else None,
    )


def extract_travel_request(text: str) -> ExtractedData:
    approver = re.search(r"Aprobado por \(jefe inmediato\)\s*(.*)", text, re.IGNORECASE)
    name = re.search(r"^Nombre\s+(.+)$", text, re.MULTILINE)
    national_id = re.search(r"^C[ée]dula\s+([\d.]+)", text, re.MULTILINE)
    total = re.search(r"Valor total solicitado\s*\$\s*([\d.,]+)", text, re.IGNORECASE)
    return ExtractedData(
        sender_name=name.group(1).strip() if name else "",
        identification=national_id.group(1) if national_id else "",
        has_official_form=bool(re.search(r"TH-F-012", text, re.IGNORECASE)),
        departure_date=_dmy_after("Fecha de salida", text),
        approver=approver.group(1).strip() if approver else "",
        approver_signed=bool(re.search(r"Firma del jefe\s*\(firmado\)", text, re.IGNORECASE)),
        total_amount=parse_amount(total.group(1)) if total else None,
    )


def extract_for(doc_type: DocumentType, text: str, company_nit: str) -> ExtractedData:
    folded = fold(text)
    if doc_type in (DocumentType.INVOICE, DocumentType.QUOTATION):
        data = extract_invoice(text, company_nit)
        if doc_type == DocumentType.QUOTATION:
            data.document_number = _first(OFFICIAL_NUMBER_RE, text) or data.document_number
            data.subtotal = data.tax = None
        return data
    if doc_type == DocumentType.TRAVEL_EXPENSE_REQUEST:
        return extract_travel_request(text)
    days, kind = extract_term(text) if doc_type == DocumentType.OVERSIGHT_NOTICE else (None, "")
    national_id = re.search(r"c[ée]dula\s*(?:No\.?)?\s*([\d.]{6,})", text, re.IGNORECASE)
    return ExtractedData(
        document_number=_first(OFFICIAL_NUMBER_RE, text),
        identification=national_id.group(1) if national_id else "",
        term_days=days,
        term_kind=kind,
        mentions_tutela=bool(TUTELA_RE.search(folded)),
    )
