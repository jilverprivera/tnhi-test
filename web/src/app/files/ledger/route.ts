import { apiFetch } from "@/shared/lib/api-client";
import { getSession } from "@/shared/lib/session";

/** The client's Excel ledger, streamed from the API. */
export async function GET() {
  if (!(await getSession())) return new Response(null, { status: 401 });
  const upstream = await apiFetch("/api/ledger/export");
  if (!upstream.ok) return new Response(null, { status: upstream.status });
  return new Response(upstream.body, {
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "Content-Disposition": upstream.headers.get("content-disposition") ?? 'attachment; filename="libro-radicacion-2026.xlsx"',
      "Cache-Control": "private, no-store",
    },
  });
}
