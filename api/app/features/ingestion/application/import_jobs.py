"""Use cases of the import queue: enqueue now, process in the background.

At month-end the mailbox can bring hundreds of e-mails; the request returns at once with a job
id and the worker turns them into proposals without blocking the clerk's screen.
"""

import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from app.features.ingestion.application.import_emails import ImportEmails
from app.features.ingestion.application.ports import JobQueue
from app.features.ingestion.domain.import_job import ImportJob, JobSource, JobState


class EnqueueImport:
    def __init__(self, queue: JobQueue):
        self._queue = queue

    def __call__(
        self, source: JobSource, actor: str, files: list[tuple[str, bytes]] | None = None
    ) -> ImportJob:
        files = files or []
        job = ImportJob(
            id=uuid.uuid4().hex,
            state=JobState.QUEUED,
            source=source,
            actor=actor,
            file_count=len(files),
            created_at=datetime.now(UTC),
        )
        self._queue.enqueue(job, files)
        return job


class ProcessNextImport:
    """Claims the oldest queued job and runs it. Returns the duration, or None if the queue is empty."""

    def __init__(
        self, queue: JobQueue, import_emails: ImportEmails, mailbox_dir: Path, on_done=None
    ):
        self._queue, self._import, self._mailbox = queue, import_emails, mailbox_dir
        self._on_done = on_done  # observability hook: (job, seconds) -> None

    def __call__(self) -> float | None:
        claimed = self._queue.claim_next()
        if claimed is None:
            return None
        job, files = claimed
        started = time.perf_counter()
        try:
            if job.source == JobSource.MAILBOX:
                files = [(p.name, p.read_bytes()) for p in sorted(self._mailbox.glob("*.eml"))]
            result = self._import(files, actor=job.actor)
            self._queue.complete(job.id, asdict(result))
        except Exception:  # noqa: BLE001 - a failed job must be recorded, never kill the worker
            self._queue.fail(job.id, "IMPORT_FAILED")
        seconds = time.perf_counter() - started
        if self._on_done:
            self._on_done(job, seconds)
        return seconds
