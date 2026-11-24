from datetime import date

from app.features.deadlines.domain.deadline import DeadlineState, deadline_state, week_bounds
from tests.conftest import inbox_files

TODAY = date(2026, 11, 18)  # Wednesday


def test_week_bounds_and_states():
    assert week_bounds(TODAY) == (date(2026, 11, 16), date(2026, 11, 22))
    assert deadline_state(TODAY, date(2026, 11, 17)) == DeadlineState.OVERDUE
    assert deadline_state(TODAY, TODAY) == DeadlineState.DUE_TODAY
    assert deadline_state(TODAY, date(2026, 11, 20)) == DeadlineState.DUE_THIS_WEEK
    assert deadline_state(TODAY, date(2026, 11, 27)) == DeadlineState.DUE_NEXT_WEEK
    assert deadline_state(TODAY, date(2026, 12, 9)) == DeadlineState.LATER


def test_weekly_report_includes_documents_not_filed_yet(container):
    container.import_emails(inbox_files(), actor="TEST")
    report = container.weekly_report(TODAY)
    this_week = {(d.filing_number, d.subject) for d in report.this_week}
    assert (
        "TAC-2026-ER-04792",
        "Certificación laboral",
    ) in this_week  # historical petition due 19-nov
    next_week = {d.document_id for d in report.next_week}
    assert {
        "11.eml__0",
        "12.eml__0",
    } <= next_week  # oversight notice (23-nov) and press petition (27-nov)
    assert report.not_filed_yet >= 2


def test_filed_deadlines_keep_their_urgency(container):
    container.import_emails(inbox_files(), actor="TEST")
    container.approve_documents(["11.eml__0"], actor="CLERK")
    deadline = next(d for d in container.list_deadlines(TODAY) if d.document_id == "11.eml__0")
    assert deadline.filing_number == "TAC-2026-ER-04818" and deadline.urgent
    assert deadline.business_days_left == 3  # 19, 20 and 23 November
