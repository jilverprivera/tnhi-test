"""An item of the filing inbox: the system's proposal plus what people did with it."""

from datetime import datetime

from pydantic import BaseModel

from app.shared.domain.models import Decision, DocumentStatus, Proposal


class InboxItem(BaseModel):
    id: str
    status: DocumentStatus
    proposal: Proposal  # what the system proposed (immutable)
    decision: Decision  # current decision; equals proposal.decision until corrected
    filing_number: str | None = None
    received_at: datetime
    notes: str = ""  # written by the clerk when correcting

    @property
    def was_corrected(self) -> bool:
        return self.decision != self.proposal.decision
