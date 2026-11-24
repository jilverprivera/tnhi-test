import { Mail } from "lucide-react";

import { outboxKindLabel } from "@/shared/i18n/es";
import type { OutboxMessageResponse } from "@/shared/lib/api-types";
import { StatusBadge, type BadgeTone } from "@/shared/ui/molecules/StatusBadge";

const TONE: Record<OutboxMessageResponse["kind"], BadgeTone> = {
  FORWARD_TO_DEPARTMENT: "primary",
  RETURN_TO_SENDER: "info",
  REPLY_EXISTING_NUMBER: "duplicate",
  FRAUD_ALERT: "danger",
  FRAUD_CONFIRMED: "danger",
};

export function OutboxMessageCard({ message }: { message: OutboxMessageResponse }) {
  return (
    <li>
      <details className="group rounded-xl border bg-card p-4 shadow-xs">
        <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2">
          <Mail aria-hidden className="size-4 text-muted-foreground" />
          <StatusBadge tone={TONE[message.kind]} label={outboxKindLabel[message.kind]} />
          <span className="min-w-0 flex-1 truncate text-label-sm">{message.subject}</span>
          <span className="text-caption text-muted-foreground">para {message.to_address}</span>
        </summary>
        <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-muted p-3 font-sans text-body-sm">{message.body}</pre>
      </details>
    </li>
  );
}
