import "server-only";

import { api } from "@/shared/lib/api-client";
import type { LedgerEntryResponse, LedgerSyncStateResponse, PageResponse } from "@/shared/lib/api-types";

import { toLedgerEntryView, toQueryString } from "../model/mappers";
import type { LedgerQueryView } from "../model/types";

export const LEDGER_PAGE_SIZE = 50;

export async function fetchLedgerPage(query: LedgerQueryView, offset: number) {
  const params = new URLSearchParams(toQueryString(query));
  params.set("limit", String(LEDGER_PAGE_SIZE));
  params.set("offset", String(offset));
  const { data } = await api<PageResponse<LedgerEntryResponse>>(`/api/ledger?${params}`);
  return { ...data, items: data.items.map(toLedgerEntryView) };
}

export async function fetchLedgerDuplicates() {
  return (await api<string[][]>("/api/ledger/duplicates")).data;
}

export async function fetchLedgerSyncState() {
  return (await api<LedgerSyncStateResponse | null>("/api/ledger/sync")).data;
}
