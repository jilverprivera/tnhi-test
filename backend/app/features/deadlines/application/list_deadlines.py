"""Use cases: open deadlines and the coordinator's weekly report.

Includes documents still waiting in the inbox: a legal term runs from reception, not from filing.
"""

from datetime import date, timedelta

from pydantic import BaseModel

from app.features.deadlines.domain.deadline import (
    Deadline,
    DeadlineState,
    deadline_state,
    week_bounds,
)
from app.features.filing.application.ports import InboxRepository
from app.features.ledger.application.ports import LedgerRepository
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.domain.models import DocumentStatus, LedgerStatus

OPEN_STATUSES = {LedgerStatus.IN_PROGRESS, LedgerStatus.ON_HOLD}
FAR_PAST = date(2000, 1, 1)


class ListDeadlines:
    def __init__(
        self, ledger: LedgerRepository, inbox: InboxRepository, calendar: BusinessCalendar
    ):
        self._ledger, self._inbox, self._calendar = ledger, inbox, calendar

    def _days_left(self, today: date, due: date) -> int:
        if due < today:
            return -self._calendar.business_days_between(due, today) - 1
        return self._calendar.business_days_between(today, due) + (
            1 if self._calendar.is_business_day(due) else 0
        )

    def __call__(
        self, today: date, start: date | None = None, end: date | None = None
    ) -> list[Deadline]:
        start, end = start or FAR_PAST, end or date.max
        result = []
        for e in self._ledger.due_between(start, end):
            if e.status not in OPEN_STATUSES:
                continue
            result.append(
                Deadline(
                    filing_number=e.filing_number,
                    document_id=e.source_document_id,
                    document_type=e.document_type,
                    department=e.department,
                    sender=e.sender,
                    subject=e.subject,
                    received_date=e.received_date,
                    due_date=e.due_date,
                    urgent=e.urgent,
                    state=deadline_state(today, e.due_date),
                    business_days_left=self._days_left(today, e.due_date),
                )
            )
        for item in self._inbox.list():
            due = item.decision.due_date
            if (
                item.status in (DocumentStatus.READY, DocumentStatus.NEEDS_REVIEW)
                and due
                and start <= due <= end
            ):
                doc = item.proposal.document
                result.append(
                    Deadline(
                        filing_number=None,
                        document_id=item.id,
                        document_type=item.decision.document_type,
                        department=item.decision.department,
                        sender=item.proposal.data.sender_name or doc.sender_name,
                        subject=doc.email_subject,
                        received_date=doc.received_at.date(),
                        due_date=due,
                        urgent=item.decision.urgent,
                        state=deadline_state(today, due),
                        business_days_left=self._days_left(today, due),
                    )
                )
        return sorted(result, key=lambda d: (d.due_date, not d.urgent))


class WeeklyReport(BaseModel):
    today: date
    week_start: date
    week_end: date
    overdue: list[Deadline]
    this_week: list[Deadline]
    next_week: list[Deadline]
    not_filed_yet: int


class BuildWeeklyReport:
    def __init__(self, list_deadlines: ListDeadlines):
        self._list = list_deadlines

    def __call__(self, today: date) -> WeeklyReport:
        monday, sunday = week_bounds(today)
        items = self._list(today, end=sunday + timedelta(days=7))
        by_state = lambda *states: [d for d in items if d.state in states]
        return WeeklyReport(
            today=today,
            week_start=monday,
            week_end=sunday,
            overdue=by_state(DeadlineState.OVERDUE),
            this_week=by_state(DeadlineState.DUE_TODAY, DeadlineState.DUE_THIS_WEEK),
            next_week=by_state(DeadlineState.DUE_NEXT_WEEK),
            not_filed_yet=sum(1 for d in items if d.filing_number is None),
        )
