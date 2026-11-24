"""An import job: e-mails waiting in the queue to be turned into proposals."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class JobState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class JobSource(StrEnum):
    MAILBOX = "MAILBOX"  # read the configured mailbox when the job runs
    UPLOAD = "UPLOAD"  # files uploaded with the job


class ImportJob(BaseModel):
    id: str
    state: JobState
    source: JobSource
    actor: str
    file_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: dict | None = None  # {"imported": [...], "skipped": [...], "failed": {...}}
    error_code: str | None = None
