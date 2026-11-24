"""An item of the filing inbox: the system's proposal plus what people did with it."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.shared.domain.models import Decision, DocumentStatus, Proposal


class HoldOutcome(StrEnum):
    RELEASED = "RELEASED"  # verified by phone with the supplier: goes on to be paid
    REJECTED = "REJECTED"  # fraud confirmed: never paid


class HoldResolution(BaseModel):
    outcome: HoldOutcome
    note: str
    actor: str
    at: datetime


class InboxItem(BaseModel):
    id: str
    status: DocumentStatus
    proposal: Proposal  # what the system proposed (immutable)
    decision: Decision  # current decision; equals proposal.decision until corrected
    filing_number: str | None = None
    received_at: datetime
    notes: str = ""  # written by the clerk when correcting
    hold_resolution: HoldResolution | None = (
        None  # the coordinator's verification of a held invoice
    )

    @property
    def is_awaiting_verification(self) -> bool:
        return (
            self.status == DocumentStatus.APPROVED
            and self.decision.action == "HOLD_FOR_VERIFICATION"
            and self.hold_resolution is None
        )

    @property
    def was_corrected(self) -> bool:
        return self.decision != self.proposal.decision
