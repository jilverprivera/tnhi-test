from app.features.audit.infrastructure.sql_audit_log import SqlAuditLog
from tests.conftest import inbox_files


def test_audit_trail_is_append_only():
    assert not any(hasattr(SqlAuditLog, m) for m in ("update", "delete", "remove"))


def test_every_mutation_leaves_an_event(container):
    container.import_emails(inbox_files(), actor="CLERK")
    container.approve_documents(["01.eml__0"], actor="CLERK")
    events = [e["event"] for e in container.list_audit()]
    assert events.count("DOCUMENT_PROPOSED") == 17
    assert "EMAILS_IMPORTED" in events and "DOCUMENT_APPROVED" in events
    approved = next(
        e for e in container.list_audit("01.eml__0") if e["event"] == "DOCUMENT_APPROVED"
    )
    assert (
        approved["actor"] == "CLERK" and approved["details"]["filing_number"] == "TAC-2026-ER-04818"
    )
