"""Use case: read the audit trail (optionally for one document)."""

from app.features.audit.application.ports import AuditLog


class ListAudit:
    def __init__(self, audit: AuditLog):
        self._audit = audit

    def __call__(self, document_id: str | None = None) -> list[dict]:
        return self._audit.list(document_id)
