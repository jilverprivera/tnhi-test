"""Response views of inbox items (driving adapter: shape for the UI)."""

from app.features.filing.domain.inbox_item import InboxItem

TEXT_PREVIEW_CHARS = 4000


def inbox_item_view(item: InboxItem, include_text: bool = False) -> dict:
    document = item.proposal.document
    view = {
        "id": item.id,
        "status": item.status,
        "filing_number": item.filing_number,
        "received_at": item.received_at.isoformat(),
        "needs_review": item.decision.needs_review,
        "was_corrected": item.was_corrected,
        "notes": item.notes,
        "document": {
            "email_file": document.email_file,
            "position": document.position,
            "name": document.name,
            "sender": document.sender,
            "sender_name": document.sender_name,
            "email_subject": document.email_subject,
            "extraction_method": document.extraction_method,
            "ocr_confidence": document.ocr_confidence,
        },
        "data": item.proposal.data.model_dump(mode="json"),
        "decision": item.decision.model_dump(mode="json"),
    }
    if include_text:
        view["document"]["text"] = document.text[:TEXT_PREVIEW_CHARS]
        view["document"]["email_body"] = document.email_body[:TEXT_PREVIEW_CHARS]
        view["proposal_decision"] = item.proposal.decision.model_dump(mode="json")
    return view
