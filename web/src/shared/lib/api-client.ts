import "server-only";

import { ApiError } from "@/shared/lib/api-error";
import type { ErrorResponse, Envelope } from "@/shared/lib/api-types";
import { getSession } from "@/shared/lib/session";

/**
 * Server-side client for the Docket API. The token lives in an httpOnly cookie and never
 * reaches the browser: Server Components read with it, Server Actions mutate with it.
 */
const API_URL = process.env.DOCKET_API_URL;

interface RequestOptions {
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  form?: FormData;
  token?: string;
}

async function authHeader(explicit?: string): Promise<Record<string, string>> {
  const token = explicit ?? (await getSession())?.token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiFetch(path: string, options: RequestOptions = {}): Promise<Response> {
  const headers: Record<string, string> = { ...(await authHeader(options.token)) };
  let body: BodyInit | undefined;
  if (options.form) {
    body = options.form;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }
  if (!API_URL) throw new ApiError("API_NOT_CONFIGURED", 0);
  try {
    return await fetch(`${API_URL}${path}`, { method: options.method ?? "GET", headers, body, cache: "no-store" });
  } catch {
    throw new ApiError("NETWORK_ERROR", 0);
  }
}

/** Calls the API and unwraps the `{code, data}` envelope; throws ApiError with the error code. */
export async function api<T>(path: string, options: RequestOptions = {}): Promise<Envelope<T>> {
  const response = await apiFetch(path, options);
  const payload = (await response.json().catch(() => ({}))) as Partial<Envelope<T>> & ErrorResponse;
  if (!response.ok) {
    throw new ApiError(payload.code ?? "HTTP_ERROR", response.status, payload.detail ?? {});
  }
  return { code: payload.code ?? "OK", data: payload.data as T };
}
