"""Ingestion endpoints: upload .eml files or read the configured mailbox folder."""

from dataclasses import asdict

from fastapi import APIRouter, UploadFile

from app.shared.infrastructure.http import ApiError, ClerkRole, ContainerDep, Envelope, ok

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
