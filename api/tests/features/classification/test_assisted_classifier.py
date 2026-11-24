"""The optional assistant: masked input, never decisive, off by default."""

from types import SimpleNamespace

from app.features.classification.application.classify_document import ClassifyDocument
from app.features.classification.infrastructure.claude_classifier import (
    ClaudeClassifier,
    mask_personal_data,
)
from app.features.classification.infrastructure.disabled_classifier import DisabledClassifier
from app.shared.domain.models import DocumentType


def test_personal_data_is_masked_before_leaving_tac():
    text = "Soy Luisa, cédula 1.032.456.789, correo luisa@tac.example, cuenta 912-345678-90, cel 3001234567"
    masked = mask_personal_data(text)
    for secret in ("1.032.456.789", "luisa@tac.example", "912-345678-90", "3001234567"):
        assert secret not in masked


class FakeMessages:
    def __init__(self, answer):
        self.answer, self.prompts = answer, []

    def create(self, **kwargs):
        self.prompts.append(kwargs["messages"][0]["content"])
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self.answer)])


def _claude(answer):
    classifier = ClaudeClassifier.__new__(ClaudeClassifier)
    classifier._client = SimpleNamespace(messages=FakeMessages(answer))
    classifier._model = "test"
    return classifier


def test_claude_answer_is_parsed_and_unknown_answers_are_ignored():
    assert _claude("PETITION").suggest_type("les pido", "x") == DocumentType.PETITION
    assert _claude("something else").suggest_type("x", "x") is None


def test_assistant_is_only_asked_when_rules_are_unsure(documents_by_email):
    claude = _claude("COMPLAINT")
    classify = ClassifyDocument(claude, "900.100.200-3", min_margin=2.0)
    clear = classify(documents_by_email["01.eml"][0])
    assert clear.classification.source == "RULES" and claude._client.messages.prompts == []


def test_disabled_by_default():
    assert (
        DisabledClassifier().enabled is False
        and DisabledClassifier().suggest_type("x", "y") is None
    )


def test_refusals_fall_back_to_rules():
    claude = _claude("PETITION")
    original = claude._client.messages.create
    claude._client.messages.create = lambda **kw: SimpleNamespace(
        **{**vars(original(**kw)), "stop_reason": "refusal"}
    )
    assert claude.suggest_type("x", "y") is None
