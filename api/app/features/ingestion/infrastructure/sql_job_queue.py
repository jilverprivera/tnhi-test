"""Adapter: import queue persisted in the database (SQLite on-prem, Postgres in the cloud)."""

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from app.features.ingestion.domain.import_job import ImportJob, JobState
from app.shared.infrastructure.db import ImportJobFileRow, ImportJobRow


def _to_job(row: ImportJobRow) -> ImportJob:
    return ImportJob(
        id=row.id,
        state=JobState(row.state),
        source=row.source,
        actor=row.actor,
        file_count=row.file_count,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        result=row.result,
        error_code=row.error_code,
    )


class SqlJobQueue:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._sessions = session_factory

    def enqueue(self, job: ImportJob, files: list[tuple[str, bytes]]) -> None:
        with self._sessions.begin() as s:
            s.add(
                ImportJobRow(
                    id=job.id,
                    state=job.state.value,
                    source=job.source.value,
                    actor=job.actor,
                    file_count=job.file_count,
                    created_at=job.created_at,
                )
            )
            s.add_all(
                ImportJobFileRow(job_id=job.id, name=name, content=content)
                for name, content in files
            )

    def claim_next(self) -> tuple[ImportJob, list[tuple[str, bytes]]] | None:
        with self._sessions.begin() as s:
            row = s.scalars(
                select(ImportJobRow)
                .where(ImportJobRow.state == JobState.QUEUED.value)
                .order_by(ImportJobRow.created_at)
            ).first()
            if row is None:
                return None
            # Compare-and-set: only one worker can move it from QUEUED to RUNNING
            claimed = s.execute(
                update(ImportJobRow)
                .where(ImportJobRow.id == row.id, ImportJobRow.state == JobState.QUEUED.value)
                .values(state=JobState.RUNNING.value, started_at=datetime.now(UTC))
            ).rowcount
            if not claimed:
                return None
            s.refresh(row)
            files = [
                (f.name, f.content)
                for f in s.scalars(
                    select(ImportJobFileRow).where(ImportJobFileRow.job_id == row.id)
                )
            ]
            return _to_job(row), files

    def complete(self, job_id: str, result: dict) -> None:
        with self._sessions.begin() as s:
            row = s.get(ImportJobRow, job_id)
            row.state, row.result, row.finished_at = JobState.DONE.value, result, datetime.now(UTC)
            s.query(ImportJobFileRow).filter(
                ImportJobFileRow.job_id == job_id
            ).delete()  # e-mails now live in the inbox

    def fail(self, job_id: str, error_code: str) -> None:
        with self._sessions.begin() as s:
            row = s.get(ImportJobRow, job_id)
            row.state, row.error_code, row.finished_at = (
                JobState.FAILED.value,
                error_code,
                datetime.now(UTC),
            )

    def get(self, job_id: str) -> ImportJob | None:
        with self._sessions() as s:
            row = s.get(ImportJobRow, job_id)
            return _to_job(row) if row else None

    def recent(self, limit: int) -> list[ImportJob]:
        with self._sessions() as s:
            rows = s.scalars(
                select(ImportJobRow).order_by(ImportJobRow.created_at.desc()).limit(limit)
            ).all()
            return [_to_job(r) for r in rows]

    def requeue_interrupted(self) -> int:
        """A job left RUNNING by a crash goes back to the queue (imports are idempotent)."""
        with self._sessions.begin() as s:
            return s.execute(
                update(ImportJobRow)
                .where(ImportJobRow.state == JobState.RUNNING.value)
                .values(state=JobState.QUEUED.value, started_at=None)
            ).rowcount

    def counts(self) -> dict[str, int]:
        with self._sessions() as s:
            rows = s.execute(
                select(ImportJobRow.state, func.count()).group_by(ImportJobRow.state)
            ).all()
        found = dict(rows)
        return {state.value: found.get(state.value, 0) for state in JobState}
