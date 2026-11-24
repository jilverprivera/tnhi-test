import { describeReason } from "@/shared/i18n/es";
import type { DecisionResponse, InboxItemResponse } from "@/shared/lib/api-types";
import { formatDate, formatMoney } from "@/shared/lib/format";

import type { DecisionView, DocumentDetailView, FieldView } from "./types";

function toDecisionView(d: DecisionResponse): DecisionView {
  return {
    documentType: d.document_type,
    department: d.department,
    action: d.action,
    dueDate: d.due_date,
    isUrgent: d.urgent,
    isLate: d.late,
    existingFilingNumber: d.existing_filing_number,
  };
}

const MISMATCH = new Set(["INVOICE_ACCOUNT_MISMATCH", "EMAIL_ACCOUNT_MISMATCH"]);

/** The fields that matter for each document type, in the clerk's reading order. */
export function fieldsFor(item: InboxItemResponse): FieldView[] {
  const { data, decision } = item;
  const codes = new Set(decision.reasons.map((r) => r.code));
  const evidence = Object.fromEntries(decision.evidence.map((e) => [e.field, e.value]));
  switch (decision.document_type) {
    case "INVOICE":
      return [
        { label: "Proveedor", value: data.sender_name || item.document.sender_name },
        { label: "NIT", value: data.identification, isMono: true },
        { label: "Factura No.", value: data.document_number, isMono: true },
        { label: "Orden de compra", value: data.purchase_order || "Sin OC", emphasis: data.purchase_order ? undefined : "warning" },
        { label: "Subtotal", value: formatMoney(data.subtotal) },
        { label: "IVA", value: formatMoney(data.tax) },
        { label: "Total", value: formatMoney(data.total_amount) },
        { label: "Fecha de expedición", value: formatDate(data.issue_date) },
        {
          label: "Cuenta en la factura",
          value: [data.bank, data.bank_account].filter(Boolean).join(" · "),
          emphasis: [...MISMATCH].some((c) => codes.has(c)) ? "danger" : undefined,
          isMono: true,
        },
        ...(evidence.master_account ? [{ label: "Cuenta en el maestro", value: evidence.master_account, isMono: true }] : []),
        ...(evidence.master_email
          ? [{ label: "Correo en el maestro", value: evidence.master_email, emphasis: codes.has("SENDER_DOMAIN_MISMATCH") ? ("danger" as const) : undefined }]
          : []),
      ];
    case "QUOTATION":
      return [
        { label: "Proveedor", value: data.sender_name || item.document.sender_name },
        { label: "NIT", value: data.identification, isMono: true },
        { label: "Cotización No.", value: data.document_number, isMono: true },
      ];
    case "TRAVEL_EXPENSE_REQUEST":
      return [
        { label: "Solicitante", value: data.sender_name || item.document.sender_name },
        { label: "Cédula", value: data.identification, isMono: true },
        { label: "Formato TH-F-012", value: data.has_official_form ? "Sí" : "No", emphasis: data.has_official_form ? undefined : "danger" },
        { label: "Aprobado por", value: data.approver || "Sin aprobación", emphasis: data.approver ? undefined : "danger" },
        { label: "Firma del jefe", value: data.approver_signed ? "Firmado" : "Sin firma", emphasis: data.approver_signed ? undefined : "danger" },
        { label: "Fecha de salida", value: formatDate(data.departure_date), emphasis: decision.late ? "warning" : undefined },
        { label: "Valor solicitado", value: formatMoney(data.total_amount) },
      ];
    case "OVERSIGHT_NOTICE":
      return [
        { label: "Oficio No.", value: data.document_number, isMono: true },
        {
          label: "Plazo del oficio",
          value: data.term_days ? `${data.term_days} días ${data.term_kind === "CALENDAR_DAYS" ? "calendario" : "hábiles"}` : "No encontrado",
          emphasis: data.term_days ? undefined : "danger",
        },
      ];
    default:
      return [
        { label: "Remitente", value: item.document.sender_name },
        { label: "Identificación", value: data.identification, isMono: true },
        ...(data.mentions_tutela ? [{ label: "Tutela", value: "Menciona tutela", emphasis: "danger" as const }] : []),
      ];
  }
}

export function toDocumentDetailView(item: InboxItemResponse): DocumentDetailView {
  const reasons = item.decision.reasons
    .map((r) => ({ code: r.code, text: describeReason(r.code, r.params), isBlocking: r.blocking }))
    .sort((a, b) => Number(b.isBlocking) - Number(a.isBlocking));
  return {
    id: item.id,
    status: item.status,
    decision: toDecisionView(item.decision),
    proposal: toDecisionView(item.proposal_decision ?? item.decision),
    wasCorrected: item.was_corrected,
    needsReview: item.needs_review,
    confidence: item.decision.confidence,
    filingNumber: item.filing_number,
    notes: item.notes,
    receivedAt: item.received_at,
    sender: item.document.sender,
    senderName: item.document.sender_name,
    subject: item.document.email_subject,
    documentName: item.document.name === "EMAIL_BODY" ? "Cuerpo del correo" : item.document.name,
    isEmailBody: item.document.name === "EMAIL_BODY",
    extractionMethod: item.document.extraction_method,
    ocrConfidence: item.document.ocr_confidence,
    text: item.document.text ?? "",
    emailBody: item.document.email_body ?? "",
    reasons,
    fields: fieldsFor(item),
    audit: (item.audit ?? []).map((a) => ({ at: a.at, actor: a.actor, event: a.event })),
  };
}
