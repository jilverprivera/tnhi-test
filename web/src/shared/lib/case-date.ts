import "server-only";

import { cache } from "react";

import { api } from "@/shared/lib/api-client";
import type { SessionResponse } from "@/shared/lib/api-types";

/**
 * "Today" as the API sees it (TAC_TODAY, or the real date when unset). The web keeps no date
 * of its own, so the header, the date pickers and the rules always agree. One call per request.
 */
export const fetchCaseToday = cache(async (): Promise<string> => (await api<SessionResponse>("/api/session")).data.today);
