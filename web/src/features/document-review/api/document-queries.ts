import "server-only";

import { api } from "@/shared/lib/api-client";
import { ApiError } from "@/shared/lib/api-error";
import type { InboxItemResponse, PageResponse } from "@/shared/lib/api-types";

import { toDocumentDetailView } from "../model/mappers";

export async function fetchDocument(id: string) {
  try {
    const { data } = await api<InboxItemResponse>(`/api/inbox/${encodeURIComponent(id)}`);
    return toDocumentDetailView(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "DOCUMENT_NOT_FOUND") return null;
    throw error;
  }
}

/** Next document that still needs the clerk, to keep her flow going after an action. */
export async function fetchNextPendingId(currentId: string): Promise<string | null> {
  const { data } = await api<PageResponse<InboxItemResponse>>("/api/inbox?status=NEEDS_REVIEW&status=READY&limit=200");
  const pending = data.items
    .filter((i) => i.id !== currentId)
    .sort((a, b) => Number(b.needs_review) - Number(a.needs_review) || a.received_at.localeCompare(b.received_at));
  return pending[0]?.id ?? null;
}
