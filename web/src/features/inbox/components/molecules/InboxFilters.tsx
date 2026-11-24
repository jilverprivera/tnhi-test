import Link from "next/link";

import { cn } from "@/shared/lib/cn";

import type { InboxFilter } from "../../model/types";

const LABEL: Record<InboxFilter, string> = {
  pending: "Pendientes",
  review: "Por revisar",
  ready: "Listos",
  approved: "Cerrados",
  all: "Todos",
};

export function InboxFilters({ active, counts }: { active: InboxFilter; counts: Record<InboxFilter, number> }) {
  return (
    <nav aria-label="Filtrar bandeja" className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0">
      <ul className="flex w-max gap-1 rounded-xl bg-muted p-1">
        {(Object.keys(LABEL) as InboxFilter[]).map((filter) => (
          <li key={filter}>
            <Link
              href={filter === "pending" ? "/inbox" : `/inbox?filter=${filter}`}
              aria-current={active === filter ? "page" : undefined}
              className={cn(
                "flex min-h-11 items-center gap-2 rounded-lg px-3 text-label-sm transition-colors",
                active === filter ? "bg-card text-foreground shadow-xs" : "text-muted-foreground hover:text-foreground",
              )}
            >
              {LABEL[filter]}
              <span className="rounded-full bg-background px-1.5 text-caption tabular">{counts[filter]}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
