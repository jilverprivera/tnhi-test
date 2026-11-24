"""Deadline endpoints for the coordinator."""

from datetime import date

from fastapi import APIRouter

from app.shared.infrastructure.http import AnyRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/deadlines", tags=["deadlines"])


@router.get("")
def list_deadlines(
    container: ContainerDep, _: AnyRole, start: date | None = None, end: date | None = None
) -> Envelope:
    today = container.settings.current_date()
    items = container.list_deadlines(today, start, end)
    return ok("DEADLINES_LISTED", [d.model_dump(mode="json") for d in items])


@router.get("/weekly-report")
def weekly_report(container: ContainerDep, _: AnyRole) -> Envelope:
    report = container.weekly_report(container.settings.current_date())
    return ok("WEEKLY_REPORT", report.model_dump(mode="json"))
