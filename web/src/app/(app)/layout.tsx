import { Suspense } from "react";

import { logoutAction, SessionNav, SessionSummary, SessionSummarySkeleton } from "@/features/session";
import { AppShell } from "@/shared/ui/organisms/AppShell";
import { Skeleton } from "@/shared/ui/primitives/skeleton";

function NavSkeleton({ variant }: { variant: "sidebar" | "tabbar" }) {
  return variant === "sidebar" ? (
    <div className="space-y-2" aria-hidden>
      {Array.from({ length: 4 }, (_, i) => (
        <Skeleton key={i} className="h-11 rounded-lg" />
      ))}
    </div>
  ) : (
    <div className="h-14" aria-hidden />
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell
      logout={logoutAction}
      sessionInfo={
        <Suspense fallback={<SessionSummarySkeleton />}>
          <SessionSummary />
        </Suspense>
      }
      sidebarNav={
        <Suspense fallback={<NavSkeleton variant="sidebar" />}>
          <SessionNav variant="sidebar" />
        </Suspense>
      }
      tabbarNav={
        <Suspense fallback={<NavSkeleton variant="tabbar" />}>
          <SessionNav variant="tabbar" />
        </Suspense>
      }
    >
      {children}
    </AppShell>
  );
}
