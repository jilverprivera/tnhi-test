import Link from "next/link";

import { departmentLabel, documentTypeLabel } from "@/shared/i18n/es";
import { cn } from "@/shared/lib/cn";
import { dateParts } from "@/shared/lib/format";
import { UrgentBadge } from "@/shared/ui/molecules/UrgentBadge";
import { StatusBadge } from "@/shared/ui/molecules/StatusBadge";

import { daysLeftLabel } from "../../model/mappers";
import type { DeadlineView } from "../../model/types";

export function DeadlineCard({ deadline: d }: { deadline: DeadlineView }) {
  const { day, month } = dateParts(d.dueDate);
  const body = (
    <>
      <div className="flex flex-col items-center justify-center rounded-lg bg-muted px-3 py-2 text-center">
        <span className="font-display text-headline-md tabular">{day}</span>
        <span className="text-caption uppercase text-muted-foreground">{month}</span>
      </div>
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          {d.isUrgent ? <UrgentBadge /> : null}
          {!d.isFiled ? <StatusBadge tone="warning" label="Aún sin radicar" /> : null}
          <span className={cn("text-label-sm", d.businessDaysLeft <= 1 ? "text-danger" : "text-muted-foreground")}>
            {daysLeftLabel(d.businessDaysLeft)}
          </span>
        </div>
        <p className="truncate text-label-md">{d.subject}</p>
        <p className="truncate text-caption text-muted-foreground">
          {documentTypeLabel[d.documentType]} · {d.sender} → {departmentLabel[d.department]}
          {d.filingNumber ? ` · ${d.filingNumber}` : ""}
        </p>
      </div>
    </>
  );
  const className = cn(
    "grid grid-cols-[4.5rem_1fr] items-center gap-3 rounded-xl border bg-card p-3 shadow-xs",
    d.isUrgent && "border-l-4 border-l-danger",
  );
  return (
    <li>
      {d.documentId ? (
        <Link href={`/documents/${encodeURIComponent(d.documentId)}`} className={cn(className, "transition-colors hover:bg-accent/50")}>
          {body}
        </Link>
      ) : (
        <div className={className}>{body}</div>
      )}
    </li>
  );
}
