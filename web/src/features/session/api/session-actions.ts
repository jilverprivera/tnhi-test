"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { api } from "@/shared/lib/api-client";
import { ApiError } from "@/shared/lib/api-error";
import type { SessionResponse } from "@/shared/lib/api-types";
import { ROLE_COOKIE, TOKEN_COOKIE } from "@/shared/lib/session";
import { ROLE_HOME } from "@/shared/ui/organisms/AppNav";

export interface LoginState {
  errorCode?: string;
}

const COOKIE = { httpOnly: true, sameSite: "lax" as const, path: "/", secure: process.env.NODE_ENV === "production", maxAge: 60 * 60 * 12 };

export async function loginAction(_: LoginState, form: FormData): Promise<LoginState> {
  const token = String(form.get("accessCode") ?? "").trim();
  if (!token) return { errorCode: "INVALID_CREDENTIALS" };
  let home: string;
  try {
    const { data } = await api<SessionResponse>("/api/session", { token });
    const store = await cookies();
    store.set({ name: TOKEN_COOKIE, value: token, ...COOKIE });
    store.set({ name: ROLE_COOKIE, value: data.role, ...COOKIE });
    home = ROLE_HOME[data.role];
  } catch (error) {
    const code = error instanceof ApiError ? error.code : "NETWORK_ERROR";
    return { errorCode: code === "UNAUTHORIZED" ? "INVALID_CREDENTIALS" : code };
  }
  redirect(home);
}

export async function logoutAction(): Promise<void> {
  const store = await cookies();
  store.delete(TOKEN_COOKIE);
  store.delete(ROLE_COOKIE);
  redirect("/login");
}
