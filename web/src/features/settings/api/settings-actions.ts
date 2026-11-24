"use server";

import { refresh } from "next/cache";

import { api } from "@/shared/lib/api-client";
import { ApiError, type ActionResult } from "@/shared/lib/api-error";

export async function replaceSupplierMasterAction(form: FormData): Promise<ActionResult<{ suppliers: number }>> {
  try {
    const { code, data } = await api<{ suppliers: number }>("/api/catalogs/suppliers", { method: "PUT", form });
    refresh();
    return { ok: true, code, data };
  } catch (error) {
    return { ok: false, code: error instanceof ApiError ? error.code : "NETWORK_ERROR" };
  }
}
