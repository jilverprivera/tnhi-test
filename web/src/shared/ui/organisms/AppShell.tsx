import Link from "next/link";

import { copy } from "@/shared/i18n/es";
import { Logo } from "@/shared/ui/atoms/Logo";
import { LogoutButton } from "@/shared/ui/organisms/LogoutButton";
import { ThemeToggle } from "@/shared/ui/organisms/ThemeToggle";

interface AppShellProps {
  /** Who is signed in; streamed in its own Suspense boundary (reads cookies). */
  sessionInfo: React.ReactNode;
  /** Role-specific navigation for the sidebar and the phone tab bar (also reads cookies). */
  sidebarNav: React.ReactNode;
  tabbarNav: React.ReactNode;
  logout: () => Promise<void>;
  children: React.ReactNode;
}

export function AppShell({ sessionInfo, sidebarNav, tabbarNav, logout, children }: AppShellProps) {
  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[15rem_1fr]">
      {/* Desktop sidebar: heavier material separates structure (apple-design §12) */}
      <aside className="sticky top-0 hidden h-dvh flex-col border-r bg-sidebar px-3 py-5 lg:flex">
        <Link href="/inbox" className="flex items-center gap-2.5 px-2">
          <Logo />
          <span className="leading-tight">
            <span className="block font-display text-headline-sm">{copy.appName}</span>
            <span className="block text-caption text-muted-foreground">{copy.company}</span>
          </span>
        </Link>
        <nav aria-label="Principal" className="mt-8 flex flex-col gap-1">
          {sidebarNav}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-col">
        {/* Header on every size: translucent material, content scrolls underneath */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-3 border-b border-border/60 bg-glass px-4 pt-[env(safe-area-inset-top)] backdrop-blur-xl backdrop-saturate-150 sm:px-6 lg:px-10">
          <Link href="/inbox" className="flex items-center gap-2 lg:hidden">
            <Logo className="size-7" />
            <span className="font-display text-headline-sm">{copy.appName}</span>
          </Link>
          <p className="hidden text-label-sm text-muted-foreground lg:block">Radicación de correspondencia</p>
          <div className="flex items-center gap-1 sm:gap-2">
            {sessionInfo}
            <span aria-hidden className="mx-1 hidden h-6 w-px bg-border sm:block" />
            <ThemeToggle />
            <LogoutButton action={logout} />
          </div>
        </header>

        <main id="main" className="w-full min-w-0 flex-1 px-4 pb-28 pt-6 sm:px-6 lg:px-10 lg:pb-12 lg:pt-8">
          {children}
        </main>

        {/* Phone tab bar: ≤5 destinations, 44px targets, safe-area aware */}
        <nav
          aria-label="Principal"
          className="fixed inset-x-0 bottom-0 z-30 grid auto-cols-fr grid-flow-col border-t border-border/60 bg-glass pb-[env(safe-area-inset-bottom)] backdrop-blur-xl backdrop-saturate-150 lg:hidden"
        >
          {tabbarNav}
        </nav>
      </div>
    </div>
  );
}
