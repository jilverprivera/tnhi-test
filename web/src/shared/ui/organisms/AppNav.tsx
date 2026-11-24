import { BookOpen, CalendarClock, Inbox, Landmark, Settings, ShieldCheck, type LucideIcon } from "lucide-react";
import Link from "next/link";

import { copy } from "@/shared/i18n/es";
import type { Role } from "@/shared/lib/api-types";
import { cn } from "@/shared/lib/cn";

export type NavKey = "inbox" | "deadlines" | "ledger" | "settings" | "verifications" | "compliance";

const NAV_ITEMS: Record<NavKey, { href: string; label: string; icon: LucideIcon }> = {
  inbox: { href: "/inbox", label: copy.nav.inbox, icon: Inbox },
  deadlines: { href: "/deadlines", label: copy.nav.deadlines, icon: CalendarClock },
  ledger: { href: "/ledger", label: copy.nav.ledger, icon: BookOpen },
  settings: { href: "/settings", label: copy.nav.settings, icon: Settings },
  verifications: { href: "/verifications", label: copy.nav.verifications, icon: ShieldCheck },
  compliance: { href: "/compliance", label: copy.nav.compliance, icon: Landmark },
};

/** Each role sees its own job first: Martha works the inbox, Dra. Herrera supervises and verifies. */
export const ROLE_NAV: Record<Role, NavKey[]> = {
  CLERK: ["inbox", "deadlines", "ledger", "settings"],
  COORDINATOR: ["deadlines", "verifications", "ledger", "inbox", "compliance"],
};

export const ROLE_HOME: Record<Role, string> = { CLERK: "/inbox", COORDINATOR: "/deadlines" };

export function isActive(pathname: string | null, href: string) {
  if (!pathname) return false;
  return pathname === href || pathname.startsWith(`${href}/`) || (href === "/inbox" && pathname.startsWith("/documents"));
}

interface AppNavProps {
  variant: "sidebar" | "tabbar";
  items: NavKey[];
  /** null while the URL streams in (no highlight yet). */
  pathname: string | null;
}

export function AppNav({ variant, items, pathname }: AppNavProps) {
  return (
    <>
      {items.map((key) => {
        const item = NAV_ITEMS[key];
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={key}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={
              variant === "sidebar"
                ? cn(
                    "flex min-h-11 items-center gap-3 rounded-lg px-3 text-label-md transition-colors active:scale-[0.98]",
                    active ? "bg-primary-soft text-primary-soft-foreground" : "text-foreground-secondary hover:bg-accent",
                  )
                : cn(
                    "flex min-h-14 flex-col items-center justify-center gap-0.5 text-caption transition-transform active:scale-95",
                    active ? "text-primary" : "text-muted-foreground",
                  )
            }
          >
            <item.icon aria-hidden className="size-5" />
            {item.label}
          </Link>
        );
      })}
    </>
  );
}
