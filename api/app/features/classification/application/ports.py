"""Classification ports."""

from typing import Protocol

from app.shared.domain.models import DocumentType


class AssistedClassifier(Protocol):
    """Validates the type of a low-confidence OCR reading. Optional; it never acts on its own."""

    @property
    def enabled(self) -> bool: ...

    def suggest_type(self, text: str, subject: str) -> DocumentType | None: ...
