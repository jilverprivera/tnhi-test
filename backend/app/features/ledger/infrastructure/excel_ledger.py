"""Adapter: the client's Excel ledger (libro-radicacion-2026.xlsx).

Rows already in the workbook are never touched; new rows are appended with the same column
order and the same cell styles, so Accounting and Legal keep reading it exactly as today.
"""

import io
import shutil
from copy import copy
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

from app.shared.domain.models import Department, DocumentType, LedgerEntry, LedgerStatus
from app.shared.infrastructure.client_vocabulary import (
    CLIENT_CODE_TO_DEPARTMENT,
    CLIENT_LABEL_TO_DOCUMENT_TYPE,
    CLIENT_LABEL_TO_LEDGER_STATUS,
    DEPARTMENT_TO_CLIENT_CODE,
    DOCUMENT_TYPE_TO_CLIENT_LABEL,
    FLAG_TO_CLIENT_NOTE,
    LEDGER_STATUS_TO_CLIENT_LABEL,
)

HEADERS = [
    "Radicado",
    "Fecha recibido",
    "Remitente",
    "NIT / Documento",
    "Tipo documental",
    "Asunto",
    "No. documento",
    "Valor total",
    "Dependencia",
    "Fecha vencimiento",
    "Estado",
    "Observaciones",
]


def _as_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip()[:10])


def _as_text(value) -> str:
    return "" if value is None else str(value).strip()


def client_notes(entry: LedgerEntry) -> str:
    """The 'Observaciones' column: people's notes plus the flags worth reading."""
    parts = [FLAG_TO_CLIENT_NOTE["URGENT"]] if entry.urgent else []
    parts += [FLAG_TO_CLIENT_NOTE[f] for f in entry.flags if f in FLAG_TO_CLIENT_NOTE]
    if entry.notes:
        parts.append(entry.notes)
    return ". ".join(parts)


def to_row(entry: LedgerEntry) -> list:
    return [
        entry.filing_number,
        entry.received_date.isoformat(),
        entry.sender,
        entry.identification,
        DOCUMENT_TYPE_TO_CLIENT_LABEL[entry.document_type],
        entry.subject,
        entry.document_number,
        entry.total_amount,
        DEPARTMENT_TO_CLIENT_CODE[entry.department],
        entry.due_date.isoformat() if entry.due_date else None,
        LEDGER_STATUS_TO_CLIENT_LABEL[entry.status],
        client_notes(entry),
    ]


def from_row(values: tuple) -> LedgerEntry:
    (
        number,
        received,
        sender,
        ident,
        doc_type,
        subject,
        doc_number,
        total,
        dept,
        due,
        status,
        notes,
    ) = (list(values) + [None] * 12)[:12]
    return LedgerEntry(
        filing_number=_as_text(number),
        received_date=_as_date(received),
        sender=_as_text(sender),
        identification=_as_text(ident),
        document_type=CLIENT_LABEL_TO_DOCUMENT_TYPE.get(_as_text(doc_type), DocumentType.OTHER),
        subject=_as_text(subject),
        document_number=_as_text(doc_number),
        total_amount=int(total) if isinstance(total, (int, float)) else None,
        department=CLIENT_CODE_TO_DEPARTMENT.get(_as_text(dept), Department.NONE),
        due_date=_as_date(due),
        status=CLIENT_LABEL_TO_LEDGER_STATUS.get(_as_text(status), LedgerStatus.DELIVERED),
        notes=_as_text(notes),
    )


class ExcelLedgerWorkbook:
    def __init__(self, template: Path, working_copy: Path):
        """`template` is the client's original file (read-only); `working_copy` is the shared file."""
        self._template = template
        self._working_copy = working_copy

    def _source(self) -> Path:
        if not self._working_copy.exists():
            self._working_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self._template, self._working_copy)
        return self._working_copy

    def read(self) -> list[LedgerEntry]:
        sheet = load_workbook(self._source(), read_only=True).worksheets[0]
        rows = sheet.iter_rows(min_row=2, values_only=True)
        return [from_row(r) for r in rows if r and r[0]]

    def render(self, entries: list[LedgerEntry]) -> bytes:
        workbook = load_workbook(self._source())
        sheet = workbook.worksheets[0]
        present = {_as_text(c.value) for c in sheet["A"][1:]}
        style_row = sheet.max_row
        for entry in entries:
            if entry.filing_number in present:
                continue
            target = sheet.max_row + 1
            for col, value in enumerate(to_row(entry), start=1):
                cell = sheet.cell(row=target, column=col, value=value)
                template_cell = sheet.cell(row=style_row, column=col)
                if template_cell.has_style:
                    cell._style = copy(template_cell._style)
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def save(self, entries: list[LedgerEntry]) -> None:
        content = self.render(entries)
        self._working_copy.write_bytes(content)
