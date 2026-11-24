import type { Action, Department, DocumentStatus, DocumentType, InboxSummaryResponse } from "@/shared/lib/api-types";

export interface InboxItemView {
  id: string;
  status: DocumentStatus;
  action: Action;
  documentType: DocumentType;
  department: Department;
  filingNumber: string | null;
  receivedAt: string;
  senderName: string;
  sender: string;
  subject: string;
  documentName: string;
  dueDate: string | null;
  isUrgent: boolean;
  isLate: boolean;
  needsReview: boolean;
  blockingReasons: string[];
  reasonCount: number;
}

export type InboxFilter = "pending" | "review" | "ready" | "approved" | "all";

export const INBOX_FILTERS: InboxFilter[] = ["pending", "review", "ready", "approved", "all"];

export const FILTER_STATUSES: Record<InboxFilter, DocumentStatus[]> = {
  pending: ["NEEDS_REVIEW", "READY"],
  review: ["NEEDS_REVIEW"],
  ready: ["READY"],
  approved: ["APPROVED", "DISCARDED"],
  all: [],
};

export function filterCounts(summary: InboxSummaryResponse): Record<InboxFilter, number> {
  const sum = (statuses: DocumentStatus[]) => statuses.reduce((n, s) => n + summary[s], 0);
  return {
    pending: sum(FILTER_STATUSES.pending),
    review: summary.NEEDS_REVIEW,
    ready: summary.READY,
    approved: sum(FILTER_STATUSES.approved),
    all: sum(["NEEDS_REVIEW", "READY", "APPROVED", "DISCARDED"]),
  };
}
