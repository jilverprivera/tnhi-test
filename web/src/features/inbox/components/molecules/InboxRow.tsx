import { ChevronRight, Paperclip } from "lucide-react";
import Link from "next/link";

import { departmentLabel, documentTypeLabel, presentationLabel } from "@/shared/i18n/es";
import { cn } from "@/shared/lib/cn";
import { formatDate, formatDateTime } from "@/shared/lib/format";
import { DocumentStatusBadge } from "@/shared/ui/molecules/DocumentStatusBadge";
import { UrgentBadge } from "@/shared/ui/molecules/UrgentBadge";
import { StatusBadge } from "@/shared/ui/molecules/StatusBadge";

import type { InboxItemView } from "../../model/types";

export function InboxRow({ item }: { item: InboxItemView }) {
  return (
    <li>
      <Link
        href={`/documents/${encodeURIComponent(item.id)}`}
        className={cn(
          "group grid gap-x-4 gap-y-2 rounded-xl border bg-card px-4 py-3.5 shadow-xs transition-[background-color,transform] duration-150 active:scale-[0.995] hover:bg-accent/50",
          "lg:grid-cols-[minmax(0,2.2fr)_minmax(0,1.3fr)_minmax(0,1fr)_auto] lg:items-center",
          item.action === "HOLD_FOR_VERIFICATION" && item.status !== "APPROVED"
            ? "border-l-4 border-l-danger"
            : item.needsReview && "border-l-4 border-l-warning",
        )}
      >
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <DocumentStatusBadge status={item.status} action={item.action} />
            {item.isUrgent ? <UrgentBadge /> : null}
            {item.isLate ? <StatusBadge tone="warning" label={presentationLabel.late} /> : null}
          </div>
          <p className="truncate text-label-md">{item.subject || item.documentName}</p>
          <p className="flex min-w-0 items-center gap-1.5 text-caption text-muted-foreground">
            <span className="truncate">{item.senderName}</span>
            <span aria-hidden>·</span>
            <Paperclip aria-hidden className="size-3 shrink-0" />
            <span className="truncate">{item.documentName}</span>
          </p>
          {item.blockingReasons[0] ? (
            <p className="text-caption text-warning">{item.blockingReasons[0]}</p>
          ) : null}
        </div>
        <div className="text-body-sm">
          <p className="text-label-sm">{documentTypeLabel[item.documentType]}</p>
          <p className="text-muted-foreground">{departmentLabel[item.department]}</p>
        </div>
        <div className="text-body-sm tabular">
          {item.filingNumber ? <p className="font-mono text-body-sm font-normal">{item.filingNumber}</p> : null}
          <p className="text-muted-foreground">Recibido {formatDateTime(item.receivedAt)}</p>
          {item.dueDate ? <p className={cn(item.isUrgent ? "text-danger" : "text-foreground-secondary")}>Vence {formatDate(item.dueDate)}</p> : null}
        </div>
        <ChevronRight aria-hidden className="hidden size-5 text-muted-foreground transition-transform group-hover:translate-x-0.5 lg:block" />
      </Link>
    </li>
  );
}
