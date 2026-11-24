"""Adapter: the client's Excel ledger (libro-radicacion-2026.xlsx) in the shared folder.

People keep working in the file (Accounting, Legal). Docket reads it with a version token, merges,
and writes back only the cells that changed, atomically, never while someone has it open.
New rows keep the same column order and cell styles, so it reads exactly as today.
"""

import io
import os
import shutil
import tempfile
from copy import copy
from dataclasses import dataclass
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
    ledger_status_from_label,
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
    """The 12 cells of a row; cells people edited by hand (overrides) are shown as they left them."""
    row = _default_row(entry)
    for column, value in entry.manual_overrides.items():
        if column in HEADERS:
            row[HEADERS.index(column)] = value
    return row


def normalize_cell(value) -> str:
    """Comparable text for any cell people may type (dates, numbers, text)."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def client_row(entry: LedgerEntry) -> list[str]:
    return [normalize_cell(v) for v in to_row(entry)]


def _cell_value(column: str, text: str):
    if column == "Valor total" and text.isdigit():
        return int(text)
    return text or None


class WorkbookLockedError(RuntimeError):
    """Someone has the file open (Excel's ~$ lock file): never overwrite their session."""


class WorkbookChangedError(RuntimeError):
    """The file changed between reading and writing: merge again."""


@dataclass(frozen=True)
class WorkbookTable:
    rows: dict[str, list[str]]  # filing number -> normalized cells
    version: str


def _default_row(entry: LedgerEntry) -> list:
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
    headers = HEADERS

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
        present = {_as_text(c.value): c.row for c in sheet["A"][1:]}
        style_row = sheet.max_row
        for entry in entries:
            if entry.filing_number in present:
                if entry.source_document_id is not None:  # a row Docket wrote: keep it in sync
                    for col, value in enumerate(to_row(entry), start=1):
                        sheet.cell(row=present[entry.filing_number], column=col, value=value)
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

    # --- bidirectional sync -----------------------------------------------------------

    @property
    def _lock_file(self) -> Path:
        return self._working_copy.with_name(f"~${self._working_copy.name}")

    def _version(self) -> str:
        stat = self._source().stat()
        return f"{stat.st_mtime_ns}:{stat.st_size}"

    def read_table(self) -> WorkbookTable:
        version = self._version()
        sheet = load_workbook(self._source(), read_only=True, data_only=True).worksheets[0]
        rows: dict[str, list[str]] = {}
        for values in sheet.iter_rows(min_row=2, max_col=len(HEADERS), values_only=True):
            cells = [
                normalize_cell(v) for v in (list(values) + [None] * len(HEADERS))[: len(HEADERS)]
            ]
            if cells[0]:
                rows[cells[0]] = cells
        return WorkbookTable(rows=rows, version=version)

    def write_table(
        self, updates: dict[str, list[str]], appends: list[list[str]], expected_version: str
    ) -> str:
        if self._lock_file.exists():
            raise WorkbookLockedError(self._lock_file.name)
        if self._version() != expected_version:
            raise WorkbookChangedError(self._working_copy.name)
        workbook = load_workbook(self._source())
        sheet = workbook.worksheets[0]
        row_of = {normalize_cell(c.value): c.row for c in sheet["A"][1:] if c.value}
        for filing_number, cells in updates.items():
            for col, (column, text) in enumerate(zip(HEADERS, cells, strict=True), start=1):
                sheet.cell(row=row_of[filing_number], column=col, value=_cell_value(column, text))
        style_row = sheet.max_row
        for cells in appends:
            target = sheet.max_row + 1
            for col, (column, text) in enumerate(zip(HEADERS, cells, strict=True), start=1):
                cell = sheet.cell(row=target, column=col, value=_cell_value(column, text))
                template_cell = sheet.cell(row=style_row, column=col)
                if template_cell.has_style:
                    cell._style = copy(template_cell._style)
        # Atomic replace: readers never see a half-written file
        fd, temporary = tempfile.mkstemp(dir=self._working_copy.parent, suffix=".xlsx")
        os.close(fd)
        workbook.save(temporary)
        if self._version() != expected_version:  # someone saved while we merged
            os.unlink(temporary)
            raise WorkbookChangedError(self._working_copy.name)
        os.replace(temporary, self._working_copy)
        return self._version()

    def render_cells(self, entry: LedgerEntry) -> list[str]:
        return client_row(entry)

    def absorb(self, entry: LedgerEntry, cells: list[str]) -> LedgerEntry:
        return absorb_cells(entry, cells)

    def parse(self, cells: list[str]) -> LedgerEntry:
        return parse_cells(cells)

    def file_bytes(self) -> bytes:
        return self._source().read_bytes()


def absorb_cells(entry: LedgerEntry, cells: list[str]) -> LedgerEntry:
    """Takes what people typed into a row: due date, status and department become data (deadlines
    and reports use them); anything else is kept as a cell override so it shows as they left it."""
    by_column = dict(zip(HEADERS, cells, strict=True))
    update: dict = {}
    due_text = by_column["Fecha vencimiento"]
    if not due_text:
        update["due_date"] = None
    else:
        try:
            update["due_date"] = date.fromisoformat(due_text[:10])
        except ValueError:
            pass  # unreadable date: kept as an override below
    status = ledger_status_from_label(by_column["Estado"])
    if status is not None:
        update["status"] = status
    department = CLIENT_CODE_TO_DEPARTMENT.get(by_column["Dependencia"])
    if department is not None:
        update["department"] = department
    absorbed = entry.model_copy(update=update | {"manual_overrides": {}})
    rendered = client_row(absorbed)
    overrides = {
        column: value
        for column, value, shown in zip(HEADERS, cells, rendered, strict=True)
        if value != shown and column != "Radicado"
    }
    return absorbed.model_copy(update={"manual_overrides": overrides})


def parse_cells(cells: list[str]) -> LedgerEntry:
    """A row typed by hand in the Excel, as a ledger entry."""
    entry = from_row(tuple(cells))
    entry = entry.model_copy(update={"flags": ["MANUAL_ENTRY"]})
    return absorb_cells(entry, cells)
