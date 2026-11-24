"""Use case: keep the ledger and the shared Excel in sync, both ways, without losing anyone's work.

- Rows typed by hand in the Excel are imported (the next filing number continues after them).
- Cells people edit (status, due date, notes...) flow into the ledger; deadlines respect them.
- Docket's changes (new rows, a verified hold) flow into the Excel cell by cell.
- Same cell changed on both sides since the last sync: people win, a conflict is recorded.
- A deleted row is restored (a filing number cannot disappear) and audited.
- The file is never written while open (lock file) nor if it changed during the merge.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.features.audit.application.ports import AuditLog
from app.features.ledger.application.ports import LedgerRepository, SyncedWorkbook, SyncStore
from app.features.ledger.domain.filing_number import parse_sequence
from app.features.ledger.domain.sync import merge_row

MAX_ATTEMPTS = 3


class SyncOutcome(StrEnum):
    SYNCED = "SYNCED"
    SYNCED_WITH_CONFLICTS = "SYNCED_WITH_CONFLICTS"
    LOCKED = "LOCKED"  # the Excel is open: changes wait until it is closed
    CHANGED_TOO_OFTEN = "CHANGED_TOO_OFTEN"


class SyncConflict(BaseModel):
    filing_number: str
    column: str


class SyncState(BaseModel):
    outcome: SyncOutcome
    at: datetime
    imported_rows: int = 0
    restored_rows: int = 0
    merged_from_excel: int = 0
    written_to_excel: int = 0
    conflicts: list[SyncConflict] = Field(default_factory=list)


class SyncLedger:
    def __init__(
        self,
        ledger: LedgerRepository,
        workbook: SyncedWorkbook,
        store: SyncStore,
        audit: AuditLog,
        prefix: str,
        locked_error: type[Exception],
        changed_error: type[Exception],
    ):
        self._ledger, self._workbook, self._store, self._audit = ledger, workbook, store, audit
        self._prefix = prefix
        self._locked, self._changed = locked_error, changed_error

    def last_state(self) -> SyncState | None:
        state = self._store.state()
        return SyncState.model_validate(state) if state else None

    def __call__(self, actor: str = "SYSTEM") -> SyncState:
        for _ in range(MAX_ATTEMPTS):
            state = self._attempt(actor)
            if state is not None:
                self._store.set_state(state.model_dump(mode="json"))
                return state
        state = SyncState(outcome=SyncOutcome.CHANGED_TOO_OFTEN, at=datetime.now(UTC))
        self._store.set_state(state.model_dump(mode="json"))
        return state

    def _attempt(self, actor: str) -> SyncState | None:
        headers = self._workbook.headers
        table = self._workbook.read_table()
        state = SyncState(outcome=SyncOutcome.SYNCED, at=datetime.now(UTC))
        entries = {e.filing_number: e for e in self._ledger.all_entries()}
        bases = self._store.bases()
        new_bases: dict[str, list[str]] = {}

        # 1. Rows people typed by hand
        for filing_number, cells in table.rows.items():
            if filing_number in entries:
                continue
            sequence = parse_sequence(filing_number, self._prefix)
            if sequence is None:
                continue  # not a filing number of this series: left untouched
            entry = self._workbook.parse(cells)
            self._ledger.append(entry, sequence)
            entries[filing_number] = entry
            new_bases[filing_number] = cells
            state.imported_rows += 1
            self._audit.record(
                actor, "LEDGER_MANUAL_ROW_IMPORTED", None, filing_number=filing_number
            )

        # 2. Merge every ledger row with the file
        updates: dict[str, list[str]] = {}
        appends: list[list[str]] = []
        for filing_number, entry in entries.items():
            if filing_number in new_bases:
                continue
            ours = self._workbook.render_cells(entry)
            theirs = table.rows.get(filing_number)
            if theirs is None:
                appends.append(ours)
                new_bases[filing_number] = ours
                if filing_number in bases:
                    state.restored_rows += 1
                    self._audit.record(
                        actor,
                        "LEDGER_ROW_RESTORED",
                        entry.source_document_id,
                        filing_number=filing_number,
                    )
                continue
            base = bases.get(filing_number, theirs)  # first sync: the file is the starting point
            merged = merge_row(headers, base, ours, theirs)
            if merged.values != ours:
                self._ledger.update(self._workbook.absorb(entry, merged.values))
                state.merged_from_excel += 1
                changed = [
                    h for h, o, m in zip(headers, ours, merged.values, strict=True) if o != m
                ]
                self._audit.record(
                    actor,
                    "LEDGER_EDIT_MERGED",
                    entry.source_document_id,
                    filing_number=filing_number,
                    columns=changed,
                )
            if merged.values != theirs:
                updates[filing_number] = merged.values
            for column in merged.conflicts:
                state.conflicts.append(SyncConflict(filing_number=filing_number, column=column))
                self._audit.record(
                    actor,
                    "LEDGER_SYNC_CONFLICT",
                    entry.source_document_id,
                    filing_number=filing_number,
                    column=column,
                )
            new_bases[filing_number] = merged.values

        # 3. Write back only if something changed on Docket's side
        if updates or appends:
            try:
                self._workbook.write_table(updates, appends, table.version)
            except self._locked:
                # Keep the bases of rows we could not write: their changes are retried next time
                self._store.set_bases(
                    {
                        fn: cells
                        for fn, cells in new_bases.items()
                        if fn not in updates and cells in (table.rows.get(fn),)
                    }
                )
                state.outcome = SyncOutcome.LOCKED
                return state
            except self._changed:
                return None  # someone saved in between: merge again
            state.written_to_excel = len(updates) + len(appends)
        self._store.set_bases(new_bases)
        if state.conflicts:
            state.outcome = SyncOutcome.SYNCED_WITH_CONFLICTS
        return state
