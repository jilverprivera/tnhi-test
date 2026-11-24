"""Text normalization shared by the classifier and the field extractor."""

import re
import unicodedata


def fold(text: str) -> str:
    """Lowercase without accents, collapsing whitespace."""
    no_accents = "".join(
        c for c in unicodedata.normalize("NFD", text or "") if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", no_accents.lower()).strip()


def parse_amount(raw: str) -> int | None:
    """'$12.600.000' or '12,600,000' -> 12600000 (Colombian pesos have no decimals here)."""
    digits = re.sub(r"[^\d]", "", raw or "")
    return int(digits) if digits else None


SPANISH_NUMBER_WORDS = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "quince": 15,
    "veinte": 20,
    "treinta": 30,
}
