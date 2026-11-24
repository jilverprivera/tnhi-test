"""Three-way merge between the ledger (Docket) and the shared Excel (people).

`base` is the row as Docket last wrote it, `ours` the row Docket would write now, `theirs` the
row currently in the file. Per cell: whoever changed it since `base` wins; if both changed the
same cell, people win (it is their book) and a conflict is recorded for review — except the
'Observaciones' column, where both texts are kept.
"""

from dataclasses import dataclass, field

NOTES_COLUMN = "Observaciones"


@dataclass
class MergeResult:
    values: list[str]
    conflicts: list[str] = field(default_factory=list)  # column names


def _merge_notes(ours: str, theirs: str) -> str:
    """Keeps everything people wrote and appends what Docket added that is not there yet."""
    missing = [part for part in ours.split(". ") if part and part not in theirs]
    return ". ".join([theirs.rstrip(". "), *missing]) if theirs else ours


def merge_row(
    headers: list[str], base: list[str], ours: list[str], theirs: list[str]
) -> MergeResult:
    result = MergeResult(values=[])
    for column, b, o, t in zip(headers, base, ours, theirs, strict=True):
        if o == t:
            result.values.append(o)
        elif b == o:  # only people changed it
            result.values.append(t)
        elif b == t:  # only Docket changed it
            result.values.append(o)
        elif column == NOTES_COLUMN:
            result.values.append(_merge_notes(o, t))
        else:  # both changed it: people win, someone reviews
            result.values.append(t)
            result.conflicts.append(column)
    return result
