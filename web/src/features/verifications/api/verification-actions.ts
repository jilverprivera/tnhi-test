"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";

export type VerificationOutcome = "release" | "reject";

export async function resolveHoldAction(id: string, outcome: VerificationOutcome, note: string): Promise<ActionResult> {
  if (note.trim().length < 5) return { ok: false, code: "VERIFICATION_NOTE_REQUIRED" };
  try {
    const { code } = await api(`/api/verifications/${encodeURIComponent(id)}/${outcome}`, {
      method: "POST",
      body: { note: note.trim() },
    });
    refresh();
    return { ok: true, code, data: undefined };
  } catch (error) {
    return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
  }
}
