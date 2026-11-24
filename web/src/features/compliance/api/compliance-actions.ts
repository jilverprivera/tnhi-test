"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";
import type { SubjectReportResponse } from "@/shared/lib/api-types";

function failure(error: unknown): ActionResult<never> {
  return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
}

export async function disposeRecordAction(filingNumber: string, recordReference: string): Promise<ActionResult> {
  try {
    const { code } = await api(`/api/retention/${encodeURIComponent(filingNumber)}/dispose`, {
      method: "POST",
      body: { record_reference: recordReference },
    });
    refresh();
    return { ok: true, code, data: undefined };
  } catch (error) {
    return failure(error);
  }
}

/** The identifier travels in the body, never in the URL (it would end up in access logs). */
export async function subjectRequestAction(identifier: string, kind: "INQUIRY" | "CLAIM"): Promise<ActionResult<SubjectReportResponse>> {
  try {
    const { code, data } = await api<SubjectReportResponse>("/api/privacy/subject-requests", {
      method: "POST",
      body: { identifier, kind },
    });
    return { ok: true, code, data };
  } catch (error) {
    return failure(error);
  }
}
