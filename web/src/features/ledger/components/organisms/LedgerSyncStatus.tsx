"use client";

import { AlertTriangle, Loader2, Lock, RefreshCw } from "lucide-react";
import { useTransition } from "react";
import { toast } from "sonner";

import { describeError } from "@/shared/i18n/es";
import type { LedgerSyncStateResponse } from "@/shared/lib/api-types";
import { formatDateTime } from "@/shared/lib/format";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/primitives/alert";
import { Button } from "@/shared/ui/primitives/button";

import { syncLedgerAction } from "../../api/ledger-actions";

/** The shared Excel is also edited by people: shows how the last merge went and lets anyone force one. */
export function LedgerSyncStatus({ state }: { state: LedgerSyncStateResponse | null }) {
  const [pending, startTransition] = useTransition();
  const sync = () =>
    startTransition(async () => {
      const result = await syncLedgerAction();
      if (!result.ok) return void toast.error(describeError(result.code));
      const s = result.data;
      if (s.outcome === "LOCKED") return void toast.warning("El Excel está abierto en otro equipo: se escribirá al cerrarlo.");
      toast.success("Libro sincronizado con el Excel compartido", {
        description: `${s.imported_rows} filas nuevas del Excel · ${s.merged_from_excel} ediciones traídas · ${s.written_to_excel} filas escritas`,
      });
    });

  const button = (
    <Button variant="outline" size="sm" onClick={sync} disabled={pending}>
      {pending ? <Loader2 aria-hidden className="animate-spin" /> : <RefreshCw aria-hidden />} Sincronizar ahora
    </Button>
  );

  if (state?.outcome === "LOCKED") {
    return (
      <Alert>
        <Lock aria-hidden />
        <AlertTitle>El Excel compartido está abierto en otro equipo</AlertTitle>
        <AlertDescription>
          <p>Docket no lo sobrescribe mientras alguien lo tenga abierto. Los radicados nuevos ya están guardados y se escribirán cuando lo cierren.</p>
          <div className="mt-2">{button}</div>
        </AlertDescription>
      </Alert>
    );
  }
  if (state?.conflicts.length) {
    return (
      <Alert>
        <AlertTriangle aria-hidden />
        <AlertTitle>Cambios cruzados para revisar</AlertTitle>
        <AlertDescription>
          <p>
            Una persona y Docket cambiaron la misma celda. Se dejó lo que escribió la persona; revise si es correcto:{" "}
            {state.conflicts.map((c) => `${c.filing_number} (${c.column})`).join(", ")}.
          </p>
          <div className="mt-2">{button}</div>
        </AlertDescription>
      </Alert>
    );
  }
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 text-caption text-muted-foreground">
      <span>
        Sincronizado con el Excel compartido{state ? ` · ${formatDateTime(state.at)}` : ""}. Las ediciones hechas en el Excel se traen
        automáticamente.
      </span>
      {button}
    </div>
  );
}
