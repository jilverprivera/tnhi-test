import { apiFetch } from "@/shared/lib/api-client";
import { getSession } from "@/shared/lib/session";

/** Streams the original attachment from the API (the token never reaches the browser). */
export async function GET(_request: Request, ctx: RouteContext<"/files/documents/[id]">) {
  if (!(await getSession())) return new Response(null, { status: 401 });
  const { id } = await ctx.params;
  const upstream = await apiFetch(`/api/inbox/${encodeURIComponent(id)}/source`);
  if (!upstream.ok) return new Response(null, { status: upstream.status });
  return new Response(upstream.body, {
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "Content-Disposition": "inline",
      "Cache-Control": "private, no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
