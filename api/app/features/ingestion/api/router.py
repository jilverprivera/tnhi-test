"""Ingestion endpoints: upload .eml files or read the configured mailbox folder."""

from dataclasses import asdict

from fastapi import APIRouter, UploadFile

from app.features.ingestion.domain.import_job import JobSource
from app.shared.infrastructure.http import AnyRole, ApiError, ClerkRole, ContainerDep, Envelope, ok

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])

MAX_EMAIL_BYTES = 25 * 1024 * 1024


@router.post("/upload")
async def upload(files: list[UploadFile], container: ContainerDep, role: ClerkRole) -> Envelope:
    payload = []
    for f in files:
        content = await f.read()
        if len(content) > MAX_EMAIL_BYTES:
            raise ApiError(413, "EMAIL_TOO_LARGE", file=f.filename)
        payload.append((f.filename or "email.eml", content))
    result = container.import_emails(payload, actor=role)
    return ok("EMAILS_IMPORTED", asdict(result))


@router.post("/mailbox")
def import_mailbox(container: ContainerDep, role: ClerkRole) -> Envelope:
    """Reads every .eml in the mailbox folder (stand-in for the real mailbox integration)."""
    folder = container.settings.inbox_dir
    if not folder.is_dir():
        raise ApiError(404, "MAILBOX_NOT_FOUND")
    files = [(p.name, p.read_bytes()) for p in sorted(folder.glob("*.eml"))]
    result = container.import_emails(files, actor=role)
    return ok("EMAILS_IMPORTED", asdict(result))


# --- Queue: month-end peaks are imported in the background -------------------------------


def _job_view(job) -> dict:
    return job.model_dump(mode="json")


@router.post("/jobs/mailbox", status_code=202)
def enqueue_mailbox(container: ContainerDep, role: ClerkRole) -> Envelope:
    if not container.settings.inbox_dir.is_dir():
        raise ApiError(404, "MAILBOX_NOT_FOUND")
    job = container.enqueue_import(JobSource.MAILBOX, actor=role)
    return ok("IMPORT_QUEUED", _job_view(job))


@router.post("/jobs/upload", status_code=202)
async def enqueue_upload(
    files: list[UploadFile], container: ContainerDep, role: ClerkRole
) -> Envelope:
    payload = []
    for f in files:
        content = await f.read()
        if len(content) > MAX_EMAIL_BYTES:
            raise ApiError(413, "EMAIL_TOO_LARGE", file=f.filename)
        payload.append((f.filename or "email.eml", content))
    job = container.enqueue_import(JobSource.UPLOAD, actor=role, files=payload)
    return ok("IMPORT_QUEUED", _job_view(job))


@router.get("/jobs")
def list_jobs(container: ContainerDep, _: AnyRole, limit: int = 20) -> Envelope:
    jobs = container.job_queue.recent(max(1, min(limit, 100)))
    return ok(
        "IMPORT_JOBS_LISTED",
        {"jobs": [_job_view(j) for j in jobs], "counts": container.job_queue.counts()},
    )


@router.get("/jobs/{job_id}")
def get_job(job_id: str, container: ContainerDep, _: AnyRole) -> Envelope:
    job = container.job_queue.get(job_id)
    if job is None:
        raise ApiError(404, "IMPORT_JOB_NOT_FOUND", id=job_id)
    return ok("IMPORT_JOB_FOUND", _job_view(job))
