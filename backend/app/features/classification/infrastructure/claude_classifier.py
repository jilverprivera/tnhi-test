"""Adapter: Claude as a second opinion for ambiguous documents (off by default).

Personal data is masked before the text leaves TAC: national IDs, NITs, account numbers,
phone numbers and e-mail addresses are replaced with placeholders.
"""

import re

from anthropic import APIError

from app.shared.domain.models import DocumentType

_MASKS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b\d{1,3}(?:\.\d{3}){2,3}(?:-\d)?\b"), "[ID]"),
    (re.compile(r"\b\d[\d-]{7,}\d\b"), "[NUMBER]"),
]
_MAX_CHARS = 6000

PROMPT = """You classify documents received by a Colombian cargo terminal's filing mailbox.
Answer with exactly one code from this list and nothing else:
{codes}

Guidance: a request for information or documents that is not a complaint from a terminal user is a
PETITION; letters from Contraloría, Procuraduría, Personería or courts are OVERSIGHT_NOTICE.

E-mail subject: {subject}
Document text:
{text}"""


def mask_personal_data(text: str) -> str:
    for pattern, placeholder in _MASKS:
        text = pattern.sub(placeholder, text)
    return text


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
                model=self._model, max_tokens=10, messages=[{"role": "user", "content": prompt}]
            )
        except APIError:  # the assistant is optional: any failure falls back to rules + review
            return None
        answer = "".join(b.text for b in response.content if b.type == "text").strip().upper()
        return DocumentType(answer) if answer in DocumentType.__members__ else None
