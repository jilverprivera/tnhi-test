"""The evaluation script reports per document and per field, and agrees with the golden tests."""

from app.evaluate import evaluate
from tests.conftest import OCR_AVAILABLE


def test_evaluation_report(imported_container):
    report = evaluate(imported_container)
    client = report["references"]["client_partial"]
    full = report["references"]["full_table"]
    assert (client["documents"], client["correct"], client["wrong"]) == (8, 8, 0)
    assert full["documents"] == 17 and full["wrong"] == 0
    assert full["correct"] == (17 if OCR_AVAILABLE else 16)
    assert full["per_field"]["action"] == 17


def test_recording_classifier_counts_answers_without_keeping_text():
    from app.evaluate import RecordingClassifier
    from app.shared.domain.models import DocumentType

    class Fake:
        enabled = True

        def __init__(self):
            self.answers = iter([DocumentType.PETITION, None])

        def suggest_type(self, text, subject):
            return next(self.answers)

    recorder = RecordingClassifier(Fake())
    assert recorder.suggest_type("texto con datos", "asunto") == DocumentType.PETITION
    assert recorder.suggest_type("otro", "asunto") is None
    assert recorder.answers == ["PETITION", None]


def test_comparison_lists_only_documents_whose_outcome_changed():
    from app.evaluate import compare

    def report(outcomes):
        results = [
            {"email": e, "document": "EMAIL_BODY", "outcome": o, "actual": {}} for e, o in outcomes
        ]
        counts = {
            "correct": sum(o == "CORRECT" for _, o in outcomes),
            "routed_to_person": sum(o == "ROUTED_TO_PERSON" for _, o in outcomes),
            "wrong": sum(o == "WRONG" for _, o in outcomes),
        }
        return {"references": {"blind": counts | {"results": results}}}

    without_ai = report([("b1", "ROUTED_TO_PERSON"), ("b2", "WRONG"), ("b3", "CORRECT")])
    with_ai = report([("b1", "CORRECT"), ("b2", "WRONG"), ("b3", "CORRECT")])
    blind = compare(without_ai, with_ai)["blind"]
    assert blind["correct"] == {"without_ai": 1, "with_ai": 2}
    assert [(c["email"], c["without_ai"], c["with_ai"]) for c in blind["changed"]] == [
        ("b1", "ROUTED_TO_PERSON", "CORRECT")
    ]
