import "server-only";

import { api } from "@/shared/lib/api-client";
import type { HeldInvoiceResponse, InboxItemResponse, InboxSummaryResponse, PageResponse } from "@/shared/lib/api-types";

import { toInboxItemView } from "../model/mappers";
import { FILTER_STATUSES, type InboxFilter } from "../model/types";

export const INBOX_PAGE_SIZE = 50;

export async function fetchInboxPage(filter: InboxFilter, offset: number) {
  const params = new URLSearchParams({ limit: String(INBOX_PAGE_SIZE), offset: String(offset) });
  FILTER_STATUSES[filter].forEach((s) => params.append("status", s));
  const { data } = await api<PageResponse<InboxItemResponse>>(`/api/inbox?${params}`);
  return { ...data, items: data.items.map(toInboxItemView) };
}

export async function fetchInboxSummary() {
  return (await api<InboxSummaryResponse>("/api/inbox/summary")).data;
}

/** Held invoices still waiting for the clerk (the coordinator verifies them after filing). */
export async function fetchHeldInInbox() {
  const { data } = await api<HeldInvoiceResponse[]>("/api/verifications");
  return data.filter((h) => h.verification_state === "PENDING_CLERK_APPROVAL").length;
}
