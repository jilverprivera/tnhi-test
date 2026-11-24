import type { LedgerEntryResponse } from "@/shared/lib/api-types";

import type { LedgerEntryView, LedgerQueryView } from "./types";

export function toLedgerEntryView(e: LedgerEntryResponse): LedgerEntryView {
  return {
    filingNumber: e.filing_number,
    receivedDate: e.received_date,
    sender: e.sender,
    identification: e.identification,
    documentType: e.document_type,
    subject: e.subject,
    documentNumber: e.document_number,
    totalAmount: e.total_amount,
    department: e.department,
    dueDate: e.due_date,
    status: e.status,
    notes: e.notes,
    isUrgent: e.urgent,
    isNew: e.source_document_id !== null,
  };
}

// "ALL" is the FilterSelect sentinel for "no filter"
const one = (v: string | string[] | undefined) => {
  const value = (Array.isArray(v) ? v[0] : v) ?? "";
  return value === "ALL" ? "" : value;
};

export function parseLedgerQuery(params: Record<string, string | string[] | undefined>): LedgerQueryView {
  return { q: one(params.q), department: one(params.department), documentType: one(params.type) };
}

export function toQueryString(query: LedgerQueryView): string {
  const p = new URLSearchParams();
  if (query.q) p.set("q", query.q);
  if (query.department) p.set("department", query.department);
  if (query.documentType) p.set("document_type", query.documentType);
  return p.toString();
}

export function parseLedgerOffset(params: Record<string, string | string[] | undefined>): number {
  const n = Number(one(params.offset));
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
}

/** URL of another page keeping the current search (the form uses `type`, the API `document_type`). */
export function ledgerPageHref(query: LedgerQueryView, offset: number): string {
  const p = new URLSearchParams();
  if (query.q) p.set("q", query.q);
  if (query.department) p.set("department", query.department);
  if (query.documentType) p.set("type", query.documentType);
  if (offset) p.set("offset", String(offset));
  const qs = p.toString();
  return qs ? `/ledger?${qs}` : "/ledger";
}
