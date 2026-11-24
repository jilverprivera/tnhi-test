"""Ingestion ports: where e-mails come from and how each file format is read."""

from typing import Protocol

from app.features.ingestion.domain.email_message import EmailMessage, ExtractedText
from app.features.ingestion.domain.import_job import ImportJob


class EmailReader(Protocol):
    def read(self, content: bytes, file_name: str) -> EmailMessage: ...


class TextExtractor(Protocol):
    def supports(self, mime_type: str, filename: str) -> bool: ...

    def extract(self, content: bytes) -> ExtractedText: ...


class JobQueue(Protocol):
    """Durable queue of import jobs: survives restarts, one worker claims a job at a time."""

    def enqueue(self, job: ImportJob, files: list[tuple[str, bytes]]) -> None: ...

    def claim_next(self) -> tuple[ImportJob, list[tuple[str, bytes]]] | None: ...

    def complete(self, job_id: str, result: dict) -> None: ...

    def fail(self, job_id: str, error_code: str) -> None: ...

    def get(self, job_id: str) -> ImportJob | None: ...

    def recent(self, limit: int) -> list[ImportJob]: ...

    def requeue_interrupted(self) -> int: ...

    def counts(self) -> dict[str, int]: ...


from app.features.ingestion.domain.import_job import ImportJob
