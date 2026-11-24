/**
 * Spanish labels for every UPPER_SNAKE_CASE code the API emits, plus UI copy.
 * The only place in the frontend where Spanish lives.
 */
import type {
  Action,
  DeadlineState,
  Department,
  DocumentStatus,
  DocumentType,
  LedgerStatus,
  OutboxKind,
  Role,
  VerificationState,
} from "@/shared/lib/api-types";

export const documentTypeLabel: Record<DocumentType, string> = {
  INVOICE: "Factura",
  TRAVEL_EXPENSE_REQUEST: "Solicitud de viáticos",
  PETITION: "Derecho de petición",
  OVERSIGHT_NOTICE: "Oficio de ente de control",
  COMPLAINT: "Queja",
  QUOTATION: "Cotización",
  ADVERTISING: "Publicidad",
  OTHER: "Sin clasificar",
};

export const departmentLabel: Record<Department, string> = {
  ACCOUNTS_PAYABLE: "Cuentas por pagar",
  PROCUREMENT: "Compras",
  HUMAN_RESOURCES: "Talento humano",
  LEGAL: "Jurídica",
  CUSTOMER_SERVICE: "Atención al usuario",
  ADMIN_COORDINATION: "Coordinación administrativa",
  SENDER: "Remitente",
  NONE: "Sin dependencia",
};

export const actionLabel: Record<Action, string> = {
  FILE: "Radicar y reenviar",
  RETURN_TO_SENDER: "Devolver al remitente",
  DO_NOT_FILE: "No radicar",
  REPLY_WITH_EXISTING_NUMBER: "Responder con radicado existente",
  HOLD_FOR_VERIFICATION: "Alertar a la coordinadora (posible fraude)",
};

export const statusLabel: Record<DocumentStatus, string> = {
  READY: "Listo",
  NEEDS_REVIEW: "Requiere revisión",
  APPROVED: "Aprobado",
  DISCARDED: "Descartado",
};

/** Status as the clerk reads it: refined by the proposed action. */
export const presentationLabel = {
  held: "Retenida: posible fraude",
  duplicate: "Duplicada",
  returned: "Devolver",
  notFiled: "No se radica",
  urgent: "Urgente",
  late: "Extemporánea",
} as const;

export const ledgerStatusLabel: Record<LedgerStatus, string> = {
  DELIVERED: "Entregado",
  IN_PROGRESS: "En trámite",
  ON_HOLD: "Retenida",
  REJECTED: "Rechazada: fraude",
  CLOSED: "Cerrado",
};

export const verificationStateLabel: Record<VerificationState, string> = {
  PENDING_CLERK_APPROVAL: "Aún en la bandeja de radicación",
  AWAITING_VERIFICATION: "Por verificar",
  RELEASED: "Liberada para pago",
  REJECTED: "Fraude confirmado",
};

export const deadlineStateLabel: Record<DeadlineState, string> = {
  OVERDUE: "Vencido",
  DUE_TODAY: "Vence hoy",
  DUE_THIS_WEEK: "Esta semana",
  DUE_NEXT_WEEK: "Próxima semana",
  LATER: "Más adelante",
};

export const outboxKindLabel: Record<OutboxKind, string> = {
  FORWARD_TO_DEPARTMENT: "Reenvío a la dependencia",
  RETURN_TO_SENDER: "Devolución al remitente",
  REPLY_EXISTING_NUMBER: "Respuesta con radicado existente",
  FRAUD_ALERT: "Alerta a la coordinadora",
  FRAUD_CONFIRMED: "Aviso de fraude confirmado",
};

export const roleLabel: Record<Role, string> = {
  CLERK: "Radicación",
  COORDINATOR: "Coordinación",
};

/** Demo users behind each access code (production: the person comes from corporate SSO). */
export const roleUser: Record<Role, { name: string; title: string }> = {
  CLERK: { name: "Martha Rojas", title: "Auxiliar administrativa · Radicación" },
  COORDINATOR: { name: "Claudia Herrera", title: "Coordinadora administrativa y financiera" },
};

export const extractionMethodLabel: Record<string, string> = {
  PDF_TEXT: "PDF con texto",
  OCR: "PDF escaneado (OCR)",
  OCR_UNAVAILABLE: "Escaneado sin OCR disponible",
  EMAIL_BODY: "Cuerpo del correo",
  DOCX: "Documento Word",
  XLSX: "Hoja de cálculo",
  HTML: "HTML",
  PLAIN_TEXT: "Texto",
  UNSUPPORTED: "Formato no soportado",
  EXTRACTION_FAILED: "No se pudo extraer el texto",
};

type Params = Record<string, string>;

/** Reason codes, in the clerk's own words. `p` carries the reason's params. */
export const reasonLabel: Record<string, (p: Params) => string> = {
  DOCUMENT_UNREADABLE: () => "No se pudo leer el documento: revíselo a mano.",
  LOW_OCR_CONFIDENCE: (p) => `La lectura del escaneado es poco confiable (${p.confidence}%).`,
  UNKNOWN_DOCUMENT_TYPE: () => "No se reconoce qué tipo de documento es.",
  AMBIGUOUS_CLASSIFICATION: (p) => `Podría ser de varios tipos (${p.candidates ?? ""}): confirme cuál es.`,
  CLASSIFIED_BY_ASSISTANT: () => "El asistente de IA sugirió el tipo: confírmelo.",
  INVOICE_MISSING_FIELDS: (p) => `A la factura le faltan datos: ${p.fields ?? ""}.`,
  INVOICE_TOTALS_MISMATCH: () => "Subtotal más IVA no da el total de la factura.",
  SUPPLIER_NOT_REGISTERED: (p) => `Proveedor no registrado en el maestro (NIT ${p.nit}): va a Compras para vincularlo.`,
  NIT_CHECK_DIGIT_INVALID: (p) => `El dígito de verificación del NIT ${p.nit} no es válido: puede ser un error de digitación.`,
  SUPPLIER_INACTIVE: (p) => `El proveedor ${p.supplier ?? ""} está INACTIVO en el maestro.`,
  INVOICE_ACCOUNT_MISMATCH: (p) => `La cuenta de la factura (${p.invoice}) no es la del maestro (${p.master}).`,
  EMAIL_ACCOUNT_MISMATCH: (p) => `El correo pide consignar a otra cuenta (${p.email}).`,
  ACCOUNT_CHANGE_ANNOUNCED: () => "El correo anuncia un cambio de cuenta bancaria.",
  SENDER_DOMAIN_MISMATCH: (p) => `El correo llega de ${p.sender}, pero el proveedor usa ${p.master}.`,
  INVOICE_DUPLICATE_IN_INBOX: (p) => `La misma factura está pendiente en la bandeja (${p.document_id}).`,
  INVOICE_DUPLICATE: (p) => `Factura ya radicada con ${p.filing_number}: no se radica de nuevo.`,
  INVOICE_WITH_PURCHASE_ORDER: (p) => `Proveedor registrado y trae orden de compra ${p.purchase_order}.`,
  INVOICE_WITHOUT_PURCHASE_ORDER: () => "No trae orden de compra: Compras debe avalarla.",
  TRAVEL_REQUEST_WITHOUT_FORM: () => "No viene en el formato TH-F-012.",
  TRAVEL_REQUEST_NOT_APPROVED: () => "No tiene la aprobación firmada del jefe inmediato.",
  TRAVEL_REQUEST_MISSING_DEPARTURE: () => "No se encontró la fecha de salida.",
  TRAVEL_REQUEST_DEPARTURE_PASSED: (p) => `La fecha de salida (${p.departure}) ya pasó.`,
  TRAVEL_REQUEST_LATE: (p) => `Extemporánea: llegó ${p.notice_days} días hábiles antes del viaje (mínimo 5).`,
  TRAVEL_REQUEST_COMPLETE: (p) => `Completa, aprobada y con ${p.notice_days} días hábiles de anticipación.`,
  PETITION_GENERAL: (p) => `Petición general: ${p.days} días hábiles.`,
  PETITION_COPIES_ONLY: (p) => `Solo pide copias o documentos: ${p.days} días hábiles.`,
  PETITION_CONSULTATION: (p) => `Es una consulta (pide un concepto): ${p.days} días hábiles.`,
  PETITION_IMPLICIT: () => "No dice «derecho de petición», pero es una solicitud: se trata como petición.",
  TUTELA_THREAT: () => "Menciona una tutela: urgente.",
  HOLIDAY_IN_TERM: (p) => `Hay festivos dentro del plazo (${p.holidays}).`,
  OVERSIGHT_BODY_URGENT: () => "Ente de control o juzgado: urgente.",
  TERM_FROM_NOTICE: (p) =>
    `Plazo tomado del oficio: ${p.days} días ${p.kind === "CALENDAR_DAYS" ? "calendario" : "hábiles"}.`,
  OVERSIGHT_TERM_AMBIGUOUS: (p) => `El oficio da ${p.days} días pero no dice si son hábiles o calendario.`,
  OVERSIGHT_TERM_NOT_FOUND: () => "No se encontró el plazo en el oficio: búsquelo y fije el vencimiento.",
  COMPLAINT_TERMINAL_USER: (p) => `Queja de un usuario del terminal: ${p.days} días hábiles.`,
  QUOTATION_TO_PROCUREMENT: () => "Las cotizaciones van a Compras.",
  ADVERTISING_NOT_FILED: () => "Publicidad: no se radica.",
  REVIEWED_BY_HUMAN: () => "Revisado y corregido por una persona.",
};

export function describeReason(code: string, params: Params = {}): string {
  return reasonLabel[code]?.(params) ?? "Hay un motivo para revisar este documento.";
}

export const errorLabel: Record<string, string> = {
  UNAUTHORIZED: "Su sesión expiró. Vuelva a ingresar.",
  FORBIDDEN: "Su rol no permite esta acción.",
  DOCUMENT_NOT_FOUND: "El documento no existe.",
  DOCUMENT_NEEDS_REVIEW: "Hay documentos que requieren revisión: apruébelos uno por uno.",
  DECISION_INCOMPLETE: "Falta elegir la dependencia antes de radicar.",
  DOCUMENT_ALREADY_CLOSED: "El documento ya fue aprobado o descartado.",
  VALIDATION_ERROR: "Revise los datos ingresados.",
  SUPPLIER_MASTER_INVALID: "El archivo del maestro no tiene las columnas esperadas.",
  MAILBOX_NOT_FOUND: "No se encontró la carpeta del buzón.",
  EMAIL_TOO_LARGE: "El correo supera el tamaño permitido.",
  NETWORK_ERROR: "No hay conexión con el servidor.",
  API_NOT_CONFIGURED: "Falta configurar la dirección del servidor (DOCKET_API_URL).",
  INVALID_CREDENTIALS: "Código de acceso incorrecto.",
  IMPORT_FAILED: "No se pudo procesar la importación. Intente de nuevo.",
  IMPORT_JOB_NOT_FOUND: "No se encontró la importación.",
  RETENTION_NOT_EXPIRED: "Aún no se cumple el tiempo de retención: no se puede eliminar.",
  DISPOSITION_NOT_ALLOWED: "La tabla de retención exige conservar este documento.",
  DISPOSAL_RECORD_REQUIRED: "Indique el acta de eliminación aprobada por el comité de archivo.",
  RECORD_NOT_FOUND: "No se encontró el radicado.",
  IDENTIFIER_TOO_SHORT: "Escriba la cédula completa o el correo del titular.",
  HOLD_REQUIRES_ESCALATION: "Una factura con posible fraude no se aprueba: use «Alertar a la Dra. Herrera».",
  NOT_A_HOLD: "Este documento no está retenido por posible fraude.",
  HOLD_NOT_PENDING: "Esta factura ya fue verificada o aún no ha sido radicada.",
  VERIFICATION_NOTE_REQUIRED: "Escriba con quién habló y qué confirmó (mínimo 5 caracteres).",
};

export function describeError(code: string): string {
  return errorLabel[code] ?? "Ocurrió un error inesperado.";
}

export const copy = {
  appName: "Docket",
  company: "Terminales Andinas de Carga",
  nav: {
    inbox: "Bandeja",
    ledger: "Libro",
    deadlines: "Vencimientos",
    settings: "Ajustes",
    verifications: "Por verificar",
    compliance: "Cumplimiento",
  },
} as const;
