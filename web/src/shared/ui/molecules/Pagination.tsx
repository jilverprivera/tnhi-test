import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

import { cn } from "@/shared/lib/cn";

interface PaginationProps {
  total: number;
  limit: number;
  offset: number;
  /** Builds the URL of another page (pagination lives in the URL, so pages can be shared). */
  hrefFor: (offset: number) => string;
  label?: string;
}

const linkClass =
  "inline-flex min-h-11 items-center gap-1 rounded-md border bg-card px-3 text-label-sm transition-colors hover:bg-accent md:min-h-10";

export function Pagination({ total, limit, offset, hrefFor, label = "Paginación" }: PaginationProps) {
  if (total <= limit) return null;
  const from = offset + 1;
  const to = Math.min(offset + limit, total);
  const hasPrevious = offset > 0;
  const hasNext = offset + limit < total;
  return (
    <nav aria-label={label} className="flex items-center justify-between gap-3">
      <p className="text-caption text-muted-foreground tabular" aria-live="polite">
        {from}–{to} de {total}
      </p>
      <div className="flex gap-2">
        {hasPrevious ? (
          <Link href={hrefFor(Math.max(0, offset - limit))} className={linkClass} rel="prev">
            <ChevronLeft aria-hidden className="size-4" /> Anterior
          </Link>
        ) : (
          <span aria-disabled="true" className={cn(linkClass, "opacity-40")}>
            <ChevronLeft aria-hidden className="size-4" /> Anterior
          </span>
        )}
        {hasNext ? (
          <Link href={hrefFor(offset + limit)} className={linkClass} rel="next">
            Siguiente <ChevronRight aria-hidden className="size-4" />
          </Link>
        ) : (
          <span aria-disabled="true" className={cn(linkClass, "opacity-40")}>
            Siguiente <ChevronRight aria-hidden className="size-4" />
          </span>
        )}
      </div>
    </nav>
  );
}
