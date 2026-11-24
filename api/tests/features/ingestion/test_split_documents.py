from datetime import UTC

from app.features.ingestion.application.split_documents import SplitDocuments
from app.features.ingestion.domain.email_message import (
    BODY_DOCUMENT_NAME,
    Attachment,
    EmailMessage,
    ExtractedText,
)
from tests.conftest import OCR_AVAILABLE


class FakeExtractor:
    def supports(self, mime_type, filename):
        return filename.endswith(".pdf")

    def extract(self, content):
        return ExtractedText(text=content.decode(), method="PDF_TEXT")


def _email(attachments, body="cuerpo"):
    from datetime import datetime

    return EmailMessage(
        file_name="x.eml",
        sender="a@b.example",
        sender_name="A",
        subject="S",
        sent_at=datetime(2026, 11, 17, tzinfo=UTC),
        body=body,
        attachments=attachments,
    )


def test_every_attachment_is_its_own_document():
    split = SplitDocuments([FakeExtractor()])
    docs = split(
        _email(
            [
                Attachment(filename=f"{n}.pdf", mime_type="application/pdf", content=n.encode())
                for n in "ab"
            ]
        )
    )
    assert [d.id for d in docs] == ["x.eml__0", "x.eml__1"]
    assert [d.text for d in docs] == ["a", "b"]


def test_body_is_the_document_when_there_are_no_attachments():
    docs = SplitDocuments([FakeExtractor()])(_email([], body="solicito copia"))
    assert (
        len(docs) == 1 and docs[0].name == BODY_DOCUMENT_NAME and docs[0].text == "solicito copia"
    )


def test_small_signature_images_are_ignored():
    logo = Attachment(filename="logo.png", mime_type="image/png", content=b"x" * 100)
    docs = SplitDocuments([FakeExtractor()])(_email([logo]))
    assert docs[0].name == BODY_DOCUMENT_NAME


def test_unsupported_format_is_flagged_not_dropped():
    docs = SplitDocuments([FakeExtractor()])(
        _email([Attachment(filename="a.zip", mime_type="application/zip", content=b"z")])
    )
    assert docs[0].extraction_method == "UNSUPPORTED"


def test_real_mailbox_yields_17_documents(documents_by_email):
    assert sum(len(d) for d in documents_by_email.values()) == 17
    assert len(documents_by_email["16.eml"]) == 2  # two invoices, two filing numbers


def test_scanned_pdf_goes_through_ocr(documents_by_email):
    scanned = documents_by_email["03.eml"][0]
    if OCR_AVAILABLE:
        assert scanned.extraction_method == "OCR" and "SE-77821" in scanned.text
    else:
        assert scanned.extraction_method == "OCR_UNAVAILABLE" and scanned.text == ""


def test_dates_are_in_bogota_time(documents_by_email):
    doc = documents_by_email["14.eml"][0]
    assert doc.received_at.isoformat() == "2026-11-17T19:41:00-05:00"


def test_corrupt_attachment_is_flagged_not_crashing():
    class Broken:
        def supports(self, mime_type, filename):
            return True

        def extract(self, content):
            raise ValueError("corrupt pdf")

    docs = SplitDocuments([Broken()])(
        _email([Attachment(filename="a.pdf", mime_type="application/pdf", content=b"%PDF")])
    )
    assert docs[0].extraction_method == "EXTRACTION_FAILED"
