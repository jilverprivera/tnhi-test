import { Suspense } from "react";

import { getSession } from "@/shared/lib/session";
import { ActiveAppNav } from "@/shared/ui/organisms/ActiveAppNav";
import { AppNav, ROLE_NAV } from "@/shared/ui/organisms/AppNav";

/** Navigation for the signed-in role (reads the session: render inside <Suspense>). */
export async function SessionNav({ variant }: { variant: "sidebar" | "tabbar" }) {
  const session = await getSession();
  const items = ROLE_NAV[session?.role ?? "CLERK"];
  return (
    <Suspense fallback={<AppNav variant={variant} items={items} pathname={null} />}>
      <ActiveAppNav variant={variant} items={items} />
    </Suspense>
  );
}
