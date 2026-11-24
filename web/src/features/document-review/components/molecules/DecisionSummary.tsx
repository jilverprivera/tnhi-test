import { actionLabel, departmentLabel, documentTypeLabel } from "@/shared/i18n/es";
import { formatDate } from "@/shared/lib/format";
import { FieldRow } from "@/shared/ui/molecules/FieldRow";

import type { DecisionView } from "../../model/types";

export function DecisionSummary({ decision }: { decision: DecisionView }) {
  return (
    <dl className="divide-y">
      <FieldRow label="Qué es" value={documentTypeLabel[decision.documentType]} />
      <FieldRow label="Va para" value={departmentLabel[decision.department]} />
      <FieldRow
        label="Acción"
        value={actionLabel[decision.action]}
        emphasis={decision.action === "HOLD_FOR_VERIFICATION" ? "danger" : undefined}
      />
      {decision.existingFilingNumber ? (
        <FieldRow label="Radicado existente" value={decision.existingFilingNumber} mono />
      ) : null}
      <FieldRow
        label="Vence"
        value={decision.dueDate ? formatDate(decision.dueDate) : "No aplica"}
        emphasis={decision.isUrgent ? "danger" : undefined}
      />
    </dl>
  );
}
