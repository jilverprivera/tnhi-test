import { describeReason } from "@/shared/i18n/es";
import type { HeldInvoiceResponse } from "@/shared/lib/api-types";

import type { HeldInvoiceView } from "./types";

const FRAUD_SIGNALS = new Set([
  "INVOICE_ACCOUNT_MISMATCH",
  "EMAIL_ACCOUNT_MISMATCH",
  "ACCOUNT_CHANGE_ANNOUNCED",
  "SENDER_DOMAIN_MISMATCH",
]);

const digits = (s: string) => s.replace(/\D/g, "");
const domain = (email: string) => email.split("@")[1]?.toLowerCase() ?? "";

export function toHeldInvoiceView(item: HeldInvoiceResponse): HeldInvoiceView {
  const master = item.master_supplier;
  const accountMismatch = !!master && digits(item.data.bank_account) !== digits(master.account_number);
  const domainMismatch = !!master && domain(item.document.sender) !== domain(master.billing_email);
  return {
    id: item.id,
    state: item.verification_state,
    filingNumber: item.filing_number,
    receivedAt: item.received_at,
    supplierName: item.data.sender_name || item.document.sender_name,
    invoiceNumber: item.data.document_number,
    totalAmount: item.data.total_amount,
    purchaseOrder: item.data.purchase_order,
    sender: item.document.sender,
    subject: item.document.email_subject,
    reasons: item.decision.reasons
      .filter((r) => FRAUD_SIGNALS.has(r.code))
      .map((r) => describeReason(r.code, r.params)),
    comparisons: master
      ? [
          {
            label: "Cuenta bancaria",
            received: [item.data.bank, item.data.bank_account].filter(Boolean).join(" · ") || "—",
            master: `${master.bank} · ${master.account_number}`,
            isMismatch: accountMismatch,
          },
          {
            label: "Correo del remitente",
            received: item.document.sender,
            master: master.billing_email,
            isMismatch: domainMismatch,
          },
        ]
      : [],
    masterContact: master ? `${master.name} · ${master.billing_email}` : "Proveedor no registrado en el maestro",
    releaseDepartment: item.release_department,
    resolution: item.hold_resolution
      ? { outcome: item.hold_resolution.outcome, note: item.hold_resolution.note, at: item.hold_resolution.at }
      : null,
  };
}

export function splitByState(items: HeldInvoiceView[]) {
  return {
    awaiting: items.filter((i) => i.state === "AWAITING_VERIFICATION"),
    withClerk: items.filter((i) => i.state === "PENDING_CLERK_APPROVAL"),
    resolved: items.filter((i) => i.state === "RELEASED" || i.state === "REJECTED"),
  };
}
