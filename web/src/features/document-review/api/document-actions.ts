"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";
import type { InboxItemResponse } from "@/shared/lib/api-types";

import { documentCorrectionSchema, type DocumentCorrectionValues } from "../model/schemas";

function failure(error: unknown): ActionResult<never> {
  return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
}

const path = (id: string) => `/api/inbox/${encodeURIComponent(id)}`;

export async function approveDocumentAction(id: string): Promise<ActionResult<{ filingNumber: string | null }>> {
  try {
    const { code, data } = await api<InboxItemResponse[]>("/api/inbox/approve", { method: "POST", body: { ids: [id] } });
    refresh();
    return { ok: true, code, data: { filingNumber: data[0]?.filing_number ?? null } };
  } catch (error) {
    return failure(error);
  }
}

export async function correctDocumentAction(id: string, values: DocumentCorrectionValues): Promise<ActionResult> {
  const parsed = documentCorrectionSchema.safeParse(values);
  if (!parsed.success) return { ok: false, code: "VALIDATION_ERROR" };
  const v = parsed.data;
  try {
    const { code } = await api(`${path(id)}/correct`, {
      method: "POST",
      body: {
        document_type: v.documentType,
        department: v.department,
        action: v.action,
        due_date: v.dueDate || null,
        clear_due_date: !v.dueDate,
        urgent: v.isUrgent,
        notes: v.notes,
      },
    });
    refresh();
    return { ok: true, code, data: undefined };
  } catch (error) {
    return failure(error);
  }
}

export async function discardDocumentAction(id: string, reason: string): Promise<ActionResult> {
  if (!reason.trim()) return { ok: false, code: "VALIDATION_ERROR" };
  try {
    const { code } = await api(`${path(id)}/discard`, { method: "POST", body: { reason: reason.trim() } });
    refresh();
    return { ok: true, code, data: undefined };
  } catch (error) {
    return failure(error);
  }
}

/** Suspected fraud: the clerk does not approve, she alerts the coordinator to verify it by phone. */
export async function escalateHoldAction(id: string): Promise<ActionResult<{ filingNumber: string | null }>> {
  try {
    const { code, data } = await api<InboxItemResponse>(`${path(id)}/escalate`, { method: "POST" });
    refresh();
    return { ok: true, code, data: { filingNumber: data.filing_number } };
  } catch (error) {
    return failure(error);
  }
}
