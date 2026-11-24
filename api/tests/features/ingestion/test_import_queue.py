"""The import queue: durable, ordered, idempotent and resilient to crashes."""

from app.features.ingestion.domain.import_job import JobSource, JobState
from tests.conftest import inbox_files


def test_mailbox_job_runs_and_records_the_result(container):
    job = container.enqueue_import(JobSource.MAILBOX, actor="CLERK")
    assert container.job_queue.get(job.id).state == JobState.QUEUED
    assert container.process_next_import() is not None
    done = container.job_queue.get(job.id)
    assert done.state == JobState.DONE and len(done.result["imported"]) == 17
    assert container.process_next_import() is None  # queue empty


def test_upload_jobs_run_in_order_and_are_idempotent(container):
    files = inbox_files()
    first = container.enqueue_import(JobSource.UPLOAD, actor="CLERK", files=files[:3])
    second = container.enqueue_import(JobSource.UPLOAD, actor="CLERK", files=files[:5])
    container.process_next_import()
    container.process_next_import()
    assert len(container.job_queue.get(first.id).result["imported"]) == 3
    result = container.job_queue.get(second.id).result
    assert len(result["imported"]) == 2 and len(result["skipped"]) == 3


def test_a_failing_job_is_recorded_and_the_queue_goes_on(container, monkeypatch):
    bad = container.enqueue_import(JobSource.UPLOAD, actor="CLERK", files=[("x.eml", b"x")])
    good = container.enqueue_import(JobSource.UPLOAD, actor="CLERK", files=inbox_files()[:1])

    def explode(*_args, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(container.process_next_import, "_import", explode)
    container.process_next_import()
    assert container.job_queue.get(bad.id).error_code == "IMPORT_FAILED"
    monkeypatch.undo()
    container.process_next_import()
    assert container.job_queue.get(good.id).state == JobState.DONE


def test_jobs_interrupted_by_a_crash_go_back_to_the_queue(container):
    job = container.enqueue_import(JobSource.MAILBOX, actor="CLERK")
    container.job_queue.claim_next()  # the process dies while RUNNING
    assert container.job_queue.get(job.id).state == JobState.RUNNING
    assert container.job_queue.requeue_interrupted() == 1
    assert container.job_queue.get(job.id).state == JobState.QUEUED
