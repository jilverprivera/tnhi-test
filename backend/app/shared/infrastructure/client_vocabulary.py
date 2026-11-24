"""Translation between the system's English codes and the client's vocabulary.

The filing ledger is consulted by Accounting and Legal exactly as it is today, so the Excel
adapter writes the client's Spanish values and department codes.
"""

from app.shared.domain.models import Department, DocumentType, LedgerStatus

DEPARTMENT_TO_CLIENT_CODE: dict[Department, str] = {
    Department.ACCOUNTS_PAYABLE: "CUENTAS_POR_PAGAR",
    Department.PROCUREMENT: "COMPRAS",
    Department.HUMAN_RESOURCES: "TALENTO_HUMANO",
    Department.LEGAL: "JURIDICA",
    Department.CUSTOMER_SERVICE: "ATENCION_USUARIO",
    Department.ADMIN_COORDINATION: "COORDINACION_ADMINISTRATIVA",
    Department.SENDER: "DEVOLVER_AL_REMITENTE",
    Department.NONE: "NO_RADICAR",
}
CLIENT_CODE_TO_DEPARTMENT = {v: k for k, v in DEPARTMENT_TO_CLIENT_CODE.items()}

DOCUMENT_TYPE_TO_CLIENT_LABEL: dict[DocumentType, str] = {
    DocumentType.INVOICE: "Factura",
    DocumentType.TRAVEL_EXPENSE_REQUEST: "Solicitud de viáticos",
    DocumentType.PETITION: "Derecho de petición",
    DocumentType.OVERSIGHT_NOTICE: "Oficio ente de control",
    DocumentType.COMPLAINT: "Queja",
    DocumentType.QUOTATION: "Cotización",
    DocumentType.ADVERTISING: "Publicidad",
    DocumentType.OTHER: "Otro",
}
CLIENT_LABEL_TO_DOCUMENT_TYPE = {v: k for k, v in DOCUMENT_TYPE_TO_CLIENT_LABEL.items()}

LEDGER_STATUS_TO_CLIENT_LABEL: dict[LedgerStatus, str] = {
    LedgerStatus.DELIVERED: "Entregado",
    LedgerStatus.IN_PROGRESS: "En trámite",
    LedgerStatus.ON_HOLD: "Retenida - verificar con proveedor",
}
CLIENT_LABEL_TO_LEDGER_STATUS = {v: k for k, v in LEDGER_STATUS_TO_CLIENT_LABEL.items()}

# How some reason codes read in the ledger's "Observaciones" column
FLAG_TO_CLIENT_NOTE: dict[str, str] = {
    "URGENT": "URGENTE",
    "TRAVEL_REQUEST_LATE": "Extemporánea",
    "SUPPLIER_NOT_REGISTERED": "Proveedor no registrado: Compras debe vincularlo",
    "INVOICE_WITHOUT_PURCHASE_ORDER": "Sin OC",
    "INVOICE_ACCOUNT_MISMATCH": "Cuenta distinta al maestro",
    "SENDER_DOMAIN_MISMATCH": "Correo de remitente no coincide con el maestro",
    "ACCOUNT_CHANGE_ANNOUNCED": "Anuncia cambio de cuenta",
    "HOLD_FOR_VERIFICATION": "Retenida: verificar por teléfono con el proveedor (Dra. Herrera)",
    "TUTELA_THREAT": "Menciona tutela",
}
