import "server-only";

import { api } from "@/shared/lib/api-client";
import type { HeldInvoiceResponse, InboxSummaryResponse, WeeklyReportResponse } from "@/shared/lib/api-types";

import { toWeeklyReportView } from "../model/mappers";

export async function fetchWeeklyReport() {
  return toWeeklyReportView((await api<WeeklyReportResponse>("/api/deadlines/weekly-report")).data);
}

/** What only the coordinator decides or watches: held invoices and the clerk's backlog. */
export async function fetchCoordinatorSummary() {
  const [held, inbox] = await Promise.all([
    api<HeldInvoiceResponse[]>("/api/verifications"),
    api<InboxSummaryResponse>("/api/inbox/summary"),
  ]);
  return {
    awaitingVerification: held.data.filter((h) => h.verification_state === "AWAITING_VERIFICATION").length,
    heldInInbox: held.data.filter((h) => h.verification_state === "PENDING_CLERK_APPROVAL").length,
    clerkBacklog: inbox.data.READY + inbox.data.NEEDS_REVIEW,
    clerkNeedsReview: inbox.data.NEEDS_REVIEW,
  };
}
