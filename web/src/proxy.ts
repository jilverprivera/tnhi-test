import { NextResponse, type NextRequest } from "next/server";

const TOKEN_COOKIE = "docket_token";
const ROLE_COOKIE = "docket_role";
const ROLE_HOME: Record<string, string> = { CLERK: "/inbox", COORDINATOR: "/deadlines" };

/** Route guard: without a session cookie, everything but /login goes to /login. */
export function proxy(request: NextRequest) {
  const isLogin = request.nextUrl.pathname.startsWith("/login");
  const hasSession = request.cookies.has(TOKEN_COOKIE);
  if (!hasSession && !isLogin) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (hasSession && (isLogin || request.nextUrl.pathname === "/")) {
    const home = ROLE_HOME[request.cookies.get(ROLE_COOKIE)?.value ?? ""] ?? "/inbox";
    return NextResponse.redirect(new URL(home, request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|icon|apple-icon|manifest.webmanifest|sw.js|offline|.*\\.(?:png|svg|ico|webmanifest)$).*)",
  ],
};
