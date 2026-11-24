"""Rule-based document classifier.

Each document type has weighted signals (Spanish phrases, since the documents are Spanish).
The result carries the score margin against the runner-up, so the caller can tell a clear
decision from a guess.
"""

import re
from dataclasses import dataclass, field

from app.features.classification.domain.text import fold
from app.shared.domain.models import DocumentType

Signal = tuple[str, float]  # (regex over folded text, weight)

SIGNALS: dict[DocumentType, list[Signal]] = {
    DocumentType.INVOICE: [
        (r"factura electronica", 3),
        (r"factura de venta", 3),
        (r"\bcufe\b", 3),
        (r"total a pagar", 2),
        (r"\bfactura\b", 1),
        (r"cuenta de cobro", 2),
    ],
    DocumentType.QUOTATION: [
        (r"\bcotizacion\b", 3),
        (r"validez de la oferta", 3),
        (r"\boferta\b", 1),
    ],
    DocumentType.TRAVEL_EXPENSE_REQUEST: [
        (r"th-f-012", 4),
        (r"\bviaticos\b", 3),
        (r"anticipo de viaticos", 2),
        (r"fecha de salida", 1),
    ],
    DocumentType.OVERSIGHT_NOTICE: [
        (r"\bcontraloria\b", 3),
        (r"\bprocuraduria\b", 3),
        (r"\bpersoneria\b", 3),
        (r"\bjuzgado\b", 3),
        (r"\boficio no\b", 2),
        (r"\brequerimiento\b", 1),
        (r"\bdespacho\b", 1),
    ],
    DocumentType.PETITION: [
        (r"derecho de peticion", 4),
        (r"ley 1755", 2),
        (r"articulo 23", 2),
        (r"\bsolicito\b", 1.5),
        (r"\bles pido\b", 1.5),
        (r"\b(me|nos) informen\b", 1.5),
        (r"se nos informe", 1.5),
        (r"solicitud de informacion", 2),
    ],
    DocumentType.COMPLAINT: [
        (r"\bqueja\b", 3),
        (r"\breclamo\b", 2),
        (r"\bexijo\b", 1.5),
        (r"\bplaca\b", 1.5),
        (r"\bpatio\b", 1),
        (r"\bdescargue\b", 1),
        (r"\bbascula\b", 1),
        (r"\btransportador", 1.5),
        (r"nadie responde", 1),
        (r"mal servicio", 1),
    ],
    DocumentType.ADVERTISING: [
        (r"\bwebinar\b", 3),
        (r"\binscribete\b", 2),
        (r"no deseas recibir", 3),
        (r"\bnovedades\b", 1.5),
        (r"\bpromocion\b", 2),
        (r"\bdescuento\b", 1.5),
        (r"\bsuscripcion\b", 1),
    ],
}

MIN_SCORE = 3.0


@dataclass(frozen=True)
class Classification:
    document_type: DocumentType
    score: float
    margin: float
    matched: dict[str, list[str]] = field(default_factory=dict)  # type -> matched patterns
    source: str = "RULES"  # "RULES" | "LLM"

    @property
    def is_confident(self) -> bool:
        return self.document_type != DocumentType.OTHER and self.score >= MIN_SCORE


def classify(text: str, subject: str = "") -> Classification:
    folded = fold(f"{subject}\n{text}")
    scores: dict[DocumentType, float] = {}
    matched: dict[str, list[str]] = {}
    for doc_type, signals in SIGNALS.items():
        hits = [pattern for pattern, _ in signals if re.search(pattern, folded)]
        scores[doc_type] = sum(w for p, w in signals if p in hits)
        if hits:
            matched[doc_type.value] = hits

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (best, best_score), (_, second_score) = ranked[0], ranked[1]
    if best_score < MIN_SCORE:
        return Classification(DocumentType.OTHER, best_score, best_score - second_score, matched)
    return Classification(best, best_score, best_score - second_score, matched)
