"""Classification ports."""

from typing import Protocol

from app.shared.domain.models import DocumentType


class AssistedClassifier(Protocol):
    """Second opinion for ambiguous free text. Optional; it never acts on its own."""

    @property
    def enabled(self) -> bool: ...

    def suggest_type(self, text: str, subject: str) -> DocumentType | None: ...
