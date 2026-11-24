"""Composes the (simulated) e-mails that follow an approval.

Message bodies are Spanish because they are addressed to TAC staff and suppliers.
"""

from app.features.catalogs.domain.catalogs import DepartmentInfo
from app.features.filing.domain.inbox_item import InboxItem
from app.features.filing.domain.outbox_message import OutboxKind, OutboxMessage
from app.shared.domain.models import Action, Department

COORDINATOR_EMAIL = "coordinacion.administrativa@terminalesandinas.example"


def compose(item: InboxItem, departments: dict[Department, DepartmentInfo]) -> list[OutboxMessage]:
    decision, document = item.decision, item.proposal.document
    reference = item.filing_number or decision.existing_filing_number or ""

    if decision.action == Action.FILE and decision.department in departments:
        due = (
            f"\nFecha de vencimiento: {decision.due_date.isoformat()}" if decision.due_date else ""
        )
        urgent = "URGENTE - " if decision.urgent else ""
        return [
            OutboxMessage(
                kind=OutboxKind.FORWARD_TO_DEPARTMENT,
                document_id=item.id,
                to_address=departments[decision.department].email,
                subject=f"{urgent}[{reference}] {document.email_subject}",
                body=(
                    f"Se remite el documento radicado con el número {reference}.\n"
                    f"Remitente: {document.sender_name} <{document.sender}>\n"
                    f"Documento: {document.name}{due}"
                ),
            )
        ]
    if decision.action == Action.HOLD_FOR_VERIFICATION:
        return [
            OutboxMessage(
                kind=OutboxKind.FRAUD_ALERT,
                document_id=item.id,
                to_address=COORDINATOR_EMAIL,
                subject=f"Verificar por teléfono antes de pagar [{reference}]",
                body=(
                    "La factura no se reenvió a ninguna dependencia: la cuenta o el remitente no "
                    "coinciden con el maestro de proveedores. Verifique por teléfono con el proveedor "
                    f"(número del maestro, no el del correo).\nRemitente: {document.sender}"
                ),
            )
        ]
    if decision.action == Action.REPLY_WITH_EXISTING_NUMBER:
        return [
            OutboxMessage(
                kind=OutboxKind.REPLY_EXISTING_NUMBER,
                document_id=item.id,
                to_address=document.sender,
                subject=f"RE: {document.email_subject}",
                body=(
                    f"Buen día. Este documento ya fue radicado con el número {reference}. "
                    "No es necesario reenviarlo; su trámite continúa con ese radicado."
                ),
            )
        ]
    if decision.action == Action.RETURN_TO_SENDER:
        return [
            OutboxMessage(
                kind=OutboxKind.RETURN_TO_SENDER,
                document_id=item.id,
                to_address=document.sender,
                subject=f"RE: {document.email_subject}",
                body=(
                    "Buen día. Su solicitud no se puede radicar: debe enviarse en el formato TH-F-012 "
                    "con la firma de aprobación del jefe inmediato, mínimo cinco días hábiles antes del viaje."
                ),
            )
        ]
    return []


def compose_hold_released(
    item: InboxItem,
    department: Department,
    departments: dict[Department, DepartmentInfo],
    note: str,
) -> list[OutboxMessage]:
    if department not in departments:
        return []
    document = item.proposal.document
    return [
        OutboxMessage(
            kind=OutboxKind.FORWARD_TO_DEPARTMENT,
            document_id=item.id,
            to_address=departments[department].email,
            subject=f"[{item.filing_number}] Factura verificada: {document.email_subject}",
            body=(
                f"La coordinación verificó por teléfono con el proveedor la factura radicada con {item.filing_number}. "
                f"Se libera para su trámite.\nNota de verificación: {note}\n"
                "Pague únicamente a la cuenta registrada en el maestro de proveedores."
            ),
        )
    ]


def compose_hold_rejected(
    item: InboxItem, departments: dict[Department, DepartmentInfo], note: str
) -> list[OutboxMessage]:
    document = item.proposal.document
    recipients = [
        d for d in (Department.ACCOUNTS_PAYABLE, Department.PROCUREMENT) if d in departments
    ]
    return [
        OutboxMessage(
            kind=OutboxKind.FRAUD_CONFIRMED,
            document_id=item.id,
            to_address=departments[d].email,
            subject=f"NO PAGAR [{item.filing_number}] intento de fraude confirmado",
            body=(
                f"La coordinación confirmó que el documento radicado con {item.filing_number} es un intento de fraude "
                f"(remitente {document.sender}). No se debe pagar ni actualizar la cuenta del proveedor.\n"
                f"Nota de verificación: {note}"
            ),
        )
        for d in recipients
    ]
