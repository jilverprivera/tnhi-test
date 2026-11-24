import { describeReason } from "@/shared/i18n/es";
import type { InboxItemResponse } from "@/shared/lib/api-types";

import type { InboxFilter, InboxItemView } from "./types";

export function toInboxItemView(item: InboxItemResponse): InboxItemView {
  const blocking = item.decision.reasons.filter((r) => r.blocking);
  return {
    id: item.id,
    status: item.status,
    action: item.decision.action,
    documentType: item.decision.document_type,
    department: item.decision.department,
    filingNumber: item.filing_number,
    receivedAt: item.received_at,
    senderName: item.data.sender_name || item.document.sender_name,
    sender: item.document.sender,
    subject: item.document.email_subject,
    documentName: item.document.name === "EMAIL_BODY" ? "Cuerpo del correo" : item.document.name,
    dueDate: item.decision.due_date,
    isUrgent: item.decision.urgent,
    isLate: item.decision.late,
    needsReview: item.needs_review,
    blockingReasons: blocking.map((r) => describeReason(r.code, r.params)),
    reasonCount: item.decision.reasons.length,
  };
}

export function parseOffset(value: string | string[] | undefined): number {
  const n = Number(Array.isArray(value) ? value[0] : value);
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 0;
}

export function parseFilter(value: string | string[] | undefined): InboxFilter {
  const v = Array.isArray(value) ? value[0] : value;
  return v === "review" || v === "ready" || v === "approved" || v === "all" ? v : "pending";
}

export function applyFilter(items: InboxItemView[], filter: InboxFilter): InboxItemView[] {
  switch (filter) {
    case "review":
      return items.filter((i) => i.status === "NEEDS_REVIEW");
    case "ready":
      return items.filter((i) => i.status === "READY");
    case "approved":
      return items.filter((i) => i.status === "APPROVED" || i.status === "DISCARDED");
    case "all":
      return items;
    default:
      return items.filter((i) => i.status === "READY" || i.status === "NEEDS_REVIEW");
  }
}

/** Needs-review first (the clerk's attention), then reception order. */
export function sortForWork(items: InboxItemView[]): InboxItemView[] {
  return [...items].sort((a, b) => {
    if (a.needsReview !== b.needsReview) return a.needsReview ? -1 : 1;
    return a.receivedAt.localeCompare(b.receivedAt);
  });
}
