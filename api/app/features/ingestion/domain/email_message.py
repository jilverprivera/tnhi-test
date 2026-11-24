"""An e-mail received in the filing mailbox and how it splits into documents."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.shared.domain.models import Document

BODY_DOCUMENT_NAME = "EMAIL_BODY"

# Attachments that are not documents (signatures, calendar invites)
_IGNORED_MIME_TYPES = ("image/gif", "text/calendar", "application/pkcs7-signature")
_MIN_IMAGE_BYTES = 15_000  # smaller images are usually e-mail signature logos


class Attachment(BaseModel):
    filename: str
    mime_type: str
    content: bytes = Field(repr=False, exclude=True)


class EmailMessage(BaseModel):
    file_name: str
    sender: str
    sender_name: str
    subject: str
    sent_at: datetime
    body: str
    attachments: list[Attachment] = Field(default_factory=list)


class ExtractedText(BaseModel):
    text: str
    method: (
        str  # PDF_TEXT, OCR, OCR_UNAVAILABLE, DOCX, XLSX, HTML, PLAIN_TEXT, EMAIL_BODY, UNSUPPORTED
    )
    ocr_confidence: float | None = None


def is_document(attachment: Attachment) -> bool:
    if attachment.mime_type in _IGNORED_MIME_TYPES:
        return False
    is_small_image = (
        attachment.mime_type.startswith("image/") and len(attachment.content) < _MIN_IMAGE_BYTES
    )
    return not is_small_image


def build_document(
    email: EmailMessage, position: int, name: str, extracted: ExtractedText
) -> Document:
    return Document(
        email_file=email.file_name,
        position=position,
        name=name,
        text=extracted.text,
        extraction_method=extracted.method,
        ocr_confidence=extracted.ocr_confidence,
        received_at=email.sent_at,
        sender=email.sender,
        sender_name=email.sender_name,
        email_subject=email.subject,
        email_body=email.body,
    )
