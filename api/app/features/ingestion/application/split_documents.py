"""Use case: turn an e-mail into fileable documents.

Business rule: every document gets its own filing number, even if several arrive in the same
e-mail. When the e-mail has no useful attachment, the document is the message body.
"""

from collections.abc import Sequence

from app.features.ingestion.application.ports import TextExtractor
from app.features.ingestion.domain.email_message import (
    BODY_DOCUMENT_NAME,
    EmailMessage,
    ExtractedText,
    build_document,
    is_document,
)
from app.shared.domain.models import Document


class SplitDocuments:
    def __init__(self, extractors: Sequence[TextExtractor]):
        self._extractors = extractors

    def _extract(self, mime_type: str, filename: str, content: bytes) -> ExtractedText:
        for extractor in self._extractors:
            if extractor.supports(mime_type, filename):
                try:
                    return extractor.extract(content)
                except Exception:  # noqa: BLE001 - a corrupt file must reach a person, not crash the import
                    return ExtractedText(text="", method="EXTRACTION_FAILED")
        return ExtractedText(text="", method="UNSUPPORTED")

    def __call__(self, email: EmailMessage) -> list[Document]:
        attachments = [a for a in email.attachments if is_document(a)]
        if not attachments:
            body = ExtractedText(text=email.body, method="EMAIL_BODY")
            return [build_document(email, 0, BODY_DOCUMENT_NAME, body)]
        return [
            build_document(email, i, a.filename, self._extract(a.mime_type, a.filename, a.content))
            for i, a in enumerate(attachments)
        ]
