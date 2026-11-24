import { presentationLabel, statusLabel } from "@/shared/i18n/es";
import type { Action, DocumentStatus } from "@/shared/lib/api-types";
import { StatusBadge, type BadgeTone } from "@/shared/ui/molecules/StatusBadge";

/** What the clerk should read at a glance: status refined by the proposed action. */
export function documentPresentation(status: DocumentStatus, action: Action): { tone: BadgeTone; label: string } {
  if (status === "APPROVED") return { tone: "primary", label: statusLabel.APPROVED };
  if (status === "DISCARDED") return { tone: "muted", label: statusLabel.DISCARDED };
  if (action === "HOLD_FOR_VERIFICATION") return { tone: "danger", label: presentationLabel.held };
  if (status === "NEEDS_REVIEW") return { tone: "warning", label: statusLabel.NEEDS_REVIEW };
  if (action === "REPLY_WITH_EXISTING_NUMBER") return { tone: "duplicate", label: presentationLabel.duplicate };
  if (action === "RETURN_TO_SENDER") return { tone: "info", label: presentationLabel.returned };
  if (action === "DO_NOT_FILE") return { tone: "muted", label: presentationLabel.notFiled };
  return { tone: "success", label: statusLabel.READY };
}

export function DocumentStatusBadge({ status, action }: { status: DocumentStatus; action: Action }) {
  const { tone, label } = documentPresentation(status, action);
  return <StatusBadge tone={tone} label={label} />;
}
