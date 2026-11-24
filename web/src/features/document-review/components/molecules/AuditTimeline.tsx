import { formatDateTime } from "@/shared/lib/format";

import type { AuditView } from "../../model/types";

const EVENT_LABEL: Record<string, string> = {
  DOCUMENT_PROPOSED: "El sistema hizo la propuesta",
  DOCUMENT_CORRECTED: "Corregido",
  DOCUMENT_APPROVED: "Aprobado y radicado",
  DOCUMENT_DISCARDED: "Descartado",
  HOLD_ESCALATED: "Alerta de posible fraude enviada a la coordinadora",
  HOLD_RELEASED: "Verificada por la coordinación: liberada para pago",
  HOLD_REJECTED: "Fraude confirmado por la coordinación",
  RECORD_DISPOSED: "Eliminado según la tabla de retención",
  LEDGER_EDIT_MERGED: "Edición hecha en el Excel compartido incorporada",
  LEDGER_MANUAL_ROW_IMPORTED: "Fila escrita a mano en el Excel incorporada",
  LEDGER_ROW_RESTORED: "Fila borrada en el Excel restaurada",
  LEDGER_SYNC_CONFLICT: "Cambio cruzado en el Excel: se dejó lo escrito por la persona",
  PRIVACY_SUBJECT_LOOKUP: "Consulta de datos personales del titular",
};
const ACTOR_LABEL: Record<string, string> = { SYSTEM: "Sistema", CLERK: "Radicación", COORDINATOR: "Coordinación", CLI: "Consola", EVALUATION: "Evaluación" };

export function AuditTimeline({ events }: { events: AuditView[] }) {
  return (
    <ol className="relative space-y-3 border-l pl-4">
      {events.map((e, i) => (
        <li key={`${e.at}-${i}`} className="text-body-sm">
          <span aria-hidden className="absolute -left-[5px] mt-1.5 size-2.5 rounded-full bg-border-strong" />
          <p>{EVENT_LABEL[e.event] ?? "Actividad registrada"}</p>
          <p className="text-caption text-muted-foreground">
            {ACTOR_LABEL[e.actor] ?? "Sistema"} · {formatDateTime(e.at)}
          </p>
        </li>
      ))}
    </ol>
  );
}
