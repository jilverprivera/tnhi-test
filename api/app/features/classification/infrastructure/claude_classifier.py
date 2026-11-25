"""Adapter: Claude validates the type of scanned documents the OCR is unsure about.

Personal data is masked before the text leaves TAC (shared/domain/privacy.py).
"""

from anthropic import APIError

from app.shared.domain.models import DocumentType
from app.shared.domain.privacy import mask_personal_data

_MAX_CHARS = 6000

PROMPT = """You classify documents received by a Colombian cargo terminal's filing mailbox.
Answer with exactly one code from this list and nothing else:
{codes}

Guidance: a request for information or documents that is not a complaint from a terminal user is a
PETITION; letters from Contraloría, Procuraduría, Personería or courts are OVERSIGHT_NOTICE.

E-mail subject: {subject}
Document text:
{text}"""


class ClaudeClassifier:
    def __init__(self, api_key: str, model: str):
        from anthropic import Anthropic

        self._client = Anthropic(api_key=api_key)
        self._model = model

    enabled = True

    def suggest_type(self, text: str, subject: str) -> DocumentType | None:
        codes = "\n".join(t.value for t in DocumentType)
        prompt = PROMPT.format(
            codes=codes,
            subject=mask_personal_data(subject),
            text=mask_personal_data(text)[:_MAX_CHARS],
        )
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=256,
                # A one-word classification needs no reasoning (Haiku 5.5 thinks by default)
                thinking={"type": "disabled"},
                messages=[{"role": "user", "content": prompt}],
            )
        except APIError:  # the assistant is optional: any failure falls back to rules + review
            return None
        if getattr(response, "stop_reason", "end_turn") != "end_turn":  # refusal, max_tokens...
            return None
        answer = "".join(b.text for b in response.content if b.type == "text").strip().upper()
        return DocumentType(answer) if answer in DocumentType.__members__ else None
