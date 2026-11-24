"""Document retention (Ley 594 de 2000, Ley General de Archivos).

Each document type has a Tabla de Retención Documental (TRD) row: years in the office archive
(gestión), years in the central archive, and the final disposition. The values below are a
STARTING PROPOSAL that TAC's Comité Interno de Archivo must approve (they live in config, not code
decisions): accounting support keeps 10 years (Código de Comercio art. 60, Ley 962 de 2005 art. 28).
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from app.shared.domain.models import DocumentType, LedgerEntry


class Disposition(StrEnum):
    CONSERVE = "CONSERVE"  # conservación total: never destroyed
    DESTROY = "DESTROY"  # eliminación once the term ends (with an approved record)
    SELECT = "SELECT"  # selección: a sample is kept, the archive committee decides


class RetentionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DUE_FOR_DISPOSITION = "DUE_FOR_DISPOSITION"
    DISPOSED = "DISPOSED"


class RetentionRule(BaseModel):
    document_type: DocumentType
    office_years: int  # archivo de gestión
    central_years: int  # archivo central
    disposition: Disposition
    basis: str

    @property
    def total_years(self) -> int:
        return self.office_years + self.central_years


DEFAULT_SCHEDULE: dict[DocumentType, RetentionRule] = {
    rule.document_type: rule
    for rule in [
        RetentionRule(
            document_type=DocumentType.INVOICE,
            office_years=2,
            central_years=8,
            disposition=Disposition.DESTROY,
            basis="Soporte contable: 10 años (C. de Co. art. 60; Ley 962 de 2005 art. 28)",
        ),
        RetentionRule(
            document_type=DocumentType.TRAVEL_EXPENSE_REQUEST,
            office_years=2,
            central_years=8,
            disposition=Disposition.DESTROY,
            basis="Soporte contable de anticipos: 10 años",
        ),
        RetentionRule(
            document_type=DocumentType.PETITION,
            office_years=2,
            central_years=8,
            disposition=Disposition.SELECT,
            basis="Peticiones (Ley 1755 de 2015): valor legal; selección por el comité de archivo",
        ),
        RetentionRule(
            document_type=DocumentType.OVERSIGHT_NOTICE,
            office_years=2,
            central_years=18,
            disposition=Disposition.CONSERVE,
            basis="Requerimientos de entes de control: conservación total",
        ),
        RetentionRule(
            document_type=DocumentType.COMPLAINT,
            office_years=2,
            central_years=3,
            disposition=Disposition.DESTROY,
            basis="Quejas de usuarios del terminal: valor administrativo",
        ),
        RetentionRule(
            document_type=DocumentType.QUOTATION,
            office_years=1,
            central_years=1,
            disposition=Disposition.DESTROY,
            basis="Cotizaciones no adjudicadas: valor administrativo",
        ),
        RetentionRule(
            document_type=DocumentType.OTHER,
            office_years=2,
            central_years=3,
            disposition=Disposition.SELECT,
            basis="Sin clasificar: lo decide el comité de archivo",
        ),
    ]
}


def add_years(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 29 February
        return day.replace(year=day.year + years, day=28)


def retention_ends(entry: LedgerEntry, rule: RetentionRule) -> date:
    """Terms count from the end of the year the record was produced (archival practice)."""
    return add_years(date(entry.received_date.year, 12, 31), rule.total_years)


def retention_status(entry: LedgerEntry, rule: RetentionRule, today: date) -> RetentionStatus:
    if "DISPOSED" in entry.flags:
        return RetentionStatus.DISPOSED
    return (
        RetentionStatus.DUE_FOR_DISPOSITION
        if today > retention_ends(entry, rule)
        else RetentionStatus.ACTIVE
    )
