import "server-only";

import { api } from "@/shared/lib/api-client";
import type {
  PageResponse,
  PersonalDataItemResponse,
  RetentionRuleResponse,
  RetentionViewResponse,
} from "@/shared/lib/api-types";

export async function fetchComplianceData(previewDate: string | null) {
  const due = new URLSearchParams({ status: "DUE_FOR_DISPOSITION", limit: "100" });
  if (previewDate) due.set("on", previewDate);
  const [schedule, dueRecords, inventory] = await Promise.all([
    api<RetentionRuleResponse[]>("/api/retention/schedule"),
    api<PageResponse<RetentionViewResponse>>(`/api/retention?${due}`),
    api<{ items: PersonalDataItemResponse[]; safeguards: string[] }>("/api/privacy/inventory"),
  ]);
  return { schedule: schedule.data, due: dueRecords.data, inventory: inventory.data };
}
