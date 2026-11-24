"""Ingestion ports: where e-mails come from and how each file format is read."""

from typing import Protocol

from app.features.ingestion.domain.email_message import EmailMessage, ExtractedText


class EmailReader(Protocol):
    def read(self, content: bytes, file_name: str) -> EmailMessage: ...


class TextExtractor(Protocol):
    def supports(self, mime_type: str, filename: str) -> bool: ...

    def extract(self, content: bytes) -> ExtractedText: ...
