"""Personal data helpers (Ley 1581 de 2012): masking before anything leaves its purpose."""

import re

_MASKS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"\b\d{1,3}(?:\.\d{3}){2,3}(?:-\d)?\b"), "[ID]"),
    (re.compile(r"\b\d[\d-]{7,}\d\b"), "[NUMBER]"),
]


def mask_personal_data(text: str) -> str:
    """Replaces e-mails, national IDs / NITs, phone and account numbers with placeholders."""
    for pattern, placeholder in _MASKS:
        text = pattern.sub(placeholder, text or "")
    return text


def mask_identifier(identifier: str) -> str:
    """Keeps the last 4 characters so a lookup can be recognized in the audit trail."""
    value = identifier.strip()
    return f"***{value[-4:]}" if len(value) > 4 else "***"
