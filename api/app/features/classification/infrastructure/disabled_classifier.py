"""Adapter used while IT has not approved AI tools: never suggests anything."""

from app.shared.domain.models import DocumentType


class DisabledClassifier:
    enabled = False

    def suggest_type(self, text: str, subject: str) -> DocumentType | None:
        return None
