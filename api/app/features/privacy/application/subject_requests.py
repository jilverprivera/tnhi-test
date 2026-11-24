"""Data subject requests (Ley 1581 de 2012): where a person's data is, and the legal term to answer.

Art. 14 (consulta): answer within 10 business days. Art. 15 (reclamo): 15 business days.
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from app.features.audit.application.ports import AuditLog
from app.features.filing.application.ports import InboxRepository
from app.features.ledger.application.ports import LedgerRepository
from app.shared.domain.business_calendar import BusinessCalendar
from app.shared.domain.identifiers import digits_only
from app.shared.domain.privacy import mask_identifier

MIN_ID_DIGITS = 6


class RequestKind(StrEnum):
    INQUIRY = "INQUIRY"  # consulta
    CLAIM = "CLAIM"  # reclamo (correction, update or deletion)


TERMS = {RequestKind.INQUIRY: 10, RequestKind.CLAIM: 15}


class IdentifierTooShortError(ValueError):
    pass


class SubjectMatch(BaseModel):
    where: str  # "LEDGER" | "INBOX"
    reference: str  # filing number or document id
    fields: list[str]
    received_date: date
    content_available: bool  # False once disposed under the retention schedule


class SubjectReport(BaseModel):
    kind: RequestKind
    identifier_masked: str
    response_due: date
    matches: list[SubjectMatch]


class FindDataSubject:
    def __init__(
        self,
        inbox: InboxRepository,
        ledger: LedgerRepository,
        calendar: BusinessCalendar,
        audit: AuditLog,
    ):
        self._inbox, self._ledger, self._calendar, self._audit = inbox, ledger, calendar, audit

    def __call__(
        self, identifier: str, kind: RequestKind, today: date, actor: str
    ) -> SubjectReport:
        value = identifier.strip().lower()
        is_email = "@" in value
        digits = digits_only(value)
        if not is_email and len(digits) < MIN_ID_DIGITS:
            raise IdentifierTooShortError(identifier)

        def id_matches(text: str) -> bool:
            return value in text.lower() if is_email else digits in digits_only(text)

        matches: list[SubjectMatch] = []
        for e in self._ledger.all_entries():
            fields = [
                f
                for f, v in (("identification", e.identification), ("sender", e.sender))
                if v and id_matches(v)
            ]
            if fields:
                matches.append(
                    SubjectMatch(
                        where="LEDGER",
                        reference=e.filing_number,
                        fields=fields,
                        received_date=e.received_date,
                        content_available="DISPOSED" not in e.flags,
                    )
                )
        for item in self._inbox.list():
            doc, data = item.proposal.document, item.proposal.data
            candidates = (
                ("sender", doc.sender),
                ("identification", data.identification),
                ("document_text", doc.text),
                ("email_body", doc.email_body),
            )
            fields = [f for f, v in candidates if v and id_matches(v)]
            if fields:
                matches.append(
                    SubjectMatch(
                        where="INBOX",
                        reference=item.id,
                        fields=fields,
                        received_date=doc.received_at.date(),
                        content_available=bool(doc.text or doc.email_body),
                    )
                )
        report = SubjectReport(
            kind=kind,
            identifier_masked=mask_identifier(identifier),
            response_due=self._calendar.add_business_days(today, TERMS[kind]),
            matches=matches,
        )
        self._audit.record(
            actor,
            "PRIVACY_SUBJECT_LOOKUP",
            None,
            kind=kind.value,
            identifier=report.identifier_masked,
            matches=len(matches),
        )
        return report
