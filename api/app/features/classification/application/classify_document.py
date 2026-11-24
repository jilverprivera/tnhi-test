"""Use case: decide what a document is and extract the fields that matter.

The deterministic classifier always runs first. Only when its margin is low (a guess) and the
assisted classifier is enabled, the LLM is asked for a second opinion; the result is still
flagged so a person confirms it.
"""

from dataclasses import dataclass

from app.features.classification.application.ports import AssistedClassifier
from app.features.classification.domain.classifier import Classification, classify
from app.features.classification.domain.field_extractor import extract_for
from app.shared.domain.models import Document, ExtractedData


@dataclass(frozen=True)
class ClassifiedDocument:
    classification: Classification
    data: ExtractedData
    is_ambiguous: bool


class ClassifyDocument:
    def __init__(self, assisted: AssistedClassifier, company_nit: str, min_margin: float):
        self._assisted = assisted
        self._company_nit = company_nit
        self._min_margin = min_margin

    def __call__(self, document: Document) -> ClassifiedDocument:
        subject = document.email_subject
        result = classify(document.text, subject)
        ambiguous = not result.is_confident or result.margin < self._min_margin

        if ambiguous and self._assisted.enabled and document.text.strip():
            suggested = self._assisted.suggest_type(document.text, subject)
            if suggested is not None:
                result = Classification(
                    suggested, result.score, result.margin, result.matched, "LLM"
                )

        data = extract_for(result.document_type, document.text, self._company_nit)
        return ClassifiedDocument(result, data, ambiguous)
