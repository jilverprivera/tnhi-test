import "server-only";

import { cookies } from "next/headers";

import type { Role } from "@/shared/lib/api-types";

export const TOKEN_COOKIE = "docket_token";
export const ROLE_COOKIE = "docket_role";

export interface Session {
  token: string;
  role: Role;
}

/** Reads the session cookies. Dynamic: call it inside a <Suspense> boundary. */
export async function getSession(): Promise<Session | null> {
  const store = await cookies();
  const token = store.get(TOKEN_COOKIE)?.value;
  const role = store.get(ROLE_COOKIE)?.value as Role | undefined;
  return token && role ? { token, role } : null;
}
