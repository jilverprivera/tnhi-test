import "server-only";

import { api } from "@/shared/lib/api-client";
import type { HeldInvoiceResponse } from "@/shared/lib/api-types";

import { toHeldInvoiceView } from "../model/mappers";

export async function fetchHeldInvoices() {
  const { data } = await api<HeldInvoiceResponse[]>("/api/verifications");
  return data.map(toHeldInvoiceView);
}
