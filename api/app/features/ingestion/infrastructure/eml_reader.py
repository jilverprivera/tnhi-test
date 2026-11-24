"""Adapter: reads e-mails stored as .eml files (RFC 5322)."""

import email
from email import policy
from email.utils import parseaddr, parsedate_to_datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.features.ingestion.domain.email_message import Attachment, EmailMessage

BOGOTA = ZoneInfo("America/Bogota")


def html_to_text(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text("\n").strip()


class EmlReader:
    def read(self, content: bytes, file_name: str) -> EmailMessage:
        msg = email.message_from_bytes(content, policy=policy.default)
        sender_name, sender = parseaddr(str(msg.get("From", "")))
        sent_at = parsedate_to_datetime(msg["Date"]).astimezone(BOGOTA)

        plain, html, attachments = "", "", []
        for part in msg.walk():
            if part.is_multipart():
                continue
            filename = part.get_filename()
            if filename or part.get_content_disposition() == "attachment":
                attachments.append(
                    Attachment(
                        filename=filename or f"attachment-{len(attachments) + 1}",
                        mime_type=part.get_content_type(),
                        content=part.get_payload(decode=True) or b"",
                    )
                )
            elif part.get_content_type() == "text/plain" and not plain:
                plain = part.get_content()
            elif part.get_content_type() == "text/html" and not html:
                html = html_to_text(part.get_content())

        return EmailMessage(
            file_name=file_name,
            sender=sender.lower(),
            sender_name=sender_name or sender,
            subject=str(msg.get("Subject", "")).strip(),
            sent_at=sent_at,
            body=(plain or html).strip(),
            attachments=attachments,
        )
