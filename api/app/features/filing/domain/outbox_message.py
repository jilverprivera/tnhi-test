"""Messages the system would send (simulated: nothing is really e-mailed)."""

from enum import StrEnum

from pydantic import BaseModel


class OutboxKind(StrEnum):
    FORWARD_TO_DEPARTMENT = "FORWARD_TO_DEPARTMENT"
    RETURN_TO_SENDER = "RETURN_TO_SENDER"
    REPLY_EXISTING_NUMBER = "REPLY_EXISTING_NUMBER"
    FRAUD_ALERT = "FRAUD_ALERT"
    FRAUD_CONFIRMED = "FRAUD_CONFIRMED"


class OutboxMessage(BaseModel):
    kind: OutboxKind
    document_id: str
    to_address: str
    subject: str
    body: str
