"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";
import type { ImportJobResponse, InboxItemResponse } from "@/shared/lib/api-types";

function failure(error: unknown): ActionResult<never> {
  return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
}

/** Imports go through the queue: the action returns at once and the screen follows the job. */
export async function enqueueMailboxImportAction(): Promise<ActionResult<ImportJobResponse>> {
  try {
    const { code, data } = await api<ImportJobResponse>("/api/ingestion/jobs/mailbox", { method: "POST" });
    return { ok: true, code, data };
  } catch (error) {
    return failure(error);
  }
}

export async function enqueueUploadImportAction(form: FormData): Promise<ActionResult<ImportJobResponse>> {
  try {
    const { code, data } = await api<ImportJobResponse>("/api/ingestion/jobs/upload", { method: "POST", form });
    return { ok: true, code, data };
  } catch (error) {
    return failure(error);
  }
}

export async function getImportJobAction(id: string): Promise<ActionResult<ImportJobResponse>> {
  try {
    const { code, data } = await api<ImportJobResponse>(`/api/ingestion/jobs/${encodeURIComponent(id)}`);
    if (data.state === "DONE" || data.state === "FAILED") refresh();
    return { ok: true, code, data };
  } catch (error) {
    return failure(error);
  }
}

export async function approveReadyAction(): Promise<ActionResult<{ approved: number; filed: number }>> {
  try {
    const { code, data } = await api<InboxItemResponse[]>("/api/inbox/approve-ready", { method: "POST" });
    refresh();
    return { ok: true, code, data: { approved: data.length, filed: data.filter((i) => i.filing_number).length } };
  } catch (error) {
    return failure(error);
  }
}
