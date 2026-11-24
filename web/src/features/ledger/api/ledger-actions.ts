"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";
import type { LedgerSyncStateResponse } from "@/shared/lib/api-types";

export async function syncLedgerAction(): Promise<ActionResult<LedgerSyncStateResponse>> {
  try {
    const { code, data } = await api<LedgerSyncStateResponse>("/api/ledger/sync", { method: "POST" });
    refresh();
    return { ok: true, code, data };
  } catch (error) {
    return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
  }
}
