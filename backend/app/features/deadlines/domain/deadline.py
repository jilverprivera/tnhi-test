"""Deadlines: what is due, for whom, and how close it is."""

from datetime import date, timedelta
from enum import StrEnum

from pydantic import BaseModel

from app.shared.domain.models import Department, DocumentType


class DeadlineState(StrEnum):
    OVERDUE = "OVERDUE"
    DUE_TODAY = "DUE_TODAY"
    DUE_THIS_WEEK = "DUE_THIS_WEEK"
    DUE_NEXT_WEEK = "DUE_NEXT_WEEK"
    LATER = "LATER"


class Deadline(BaseModel):
    filing_number: str | None  # None => still in the inbox, not filed yet
    document_id: str | None
    document_type: DocumentType
    department: Department
    sender: str
    subject: str
    received_date: date
    due_date: date
    urgent: bool
    state: DeadlineState
    business_days_left: int


def week_bounds(today: date) -> tuple[date, date]:
    monday = today - timedelta(days=today.weekday())
    return monday, monday + timedelta(days=6)


def deadline_state(today: date, due: date) -> DeadlineState:
    _monday, sunday = week_bounds(today)
    if due < today:
        return DeadlineState.OVERDUE
    if due == today:
        return DeadlineState.DUE_TODAY
    if due <= sunday:
        return DeadlineState.DUE_THIS_WEEK
    if due <= sunday + timedelta(days=7):
        return DeadlineState.DUE_NEXT_WEEK
    return DeadlineState.LATER
