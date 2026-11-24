import "server-only";

import { api } from "@/shared/lib/api-client";
import type { DepartmentResponse, ImportJobResponse, OutboxMessageResponse, ReadinessResponse, SupplierResponse } from "@/shared/lib/api-types";
import { apiFetch } from "@/shared/lib/api-client";

export async function fetchSettingsData() {
  const [suppliers, departments, outbox, health] = await Promise.all([
    api<SupplierResponse[]>("/api/catalogs/suppliers"),
    api<DepartmentResponse[]>("/api/catalogs/departments"),
    api<OutboxMessageResponse[]>("/api/outbox"),
    api<{ llm_enabled: boolean }>("/api/health"),
  ]);
  return {
    suppliers: suppliers.data,
    departments: departments.data,
    outbox: outbox.data,
    isLlmEnabled: health.data.llm_enabled,
  };
}

/** Readiness answers 503 when something is down: read the body either way. */
export async function fetchSystemStatus() {
  const [readyResponse, jobs] = await Promise.all([
    apiFetch("/api/ready"),
    api<{ jobs: ImportJobResponse[]; counts: Record<string, number> }>("/api/ingestion/jobs?limit=5"),
  ]);
  const ready = (await readyResponse.json()) as { code: string; data: ReadinessResponse };
  return { code: ready.code, checks: ready.data.checks, jobs: jobs.data.jobs, queue: jobs.data.counts };
}
