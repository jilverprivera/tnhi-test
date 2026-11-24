import { CheckCircle2, XCircle } from "lucide-react";

import { cn } from "@/shared/lib/cn";

import type { ComparisonView } from "../../model/types";

/** What arrived vs. what the ERP master says: the evidence for the phone call. */
export function ComparisonTable({ rows }: { rows: ComparisonView[] }) {
  return (
    <div className="overflow-hidden rounded-lg border">
      <div className="hidden grid-cols-[10rem_1fr_1fr] bg-muted px-3 py-2 text-label-sm text-muted-foreground sm:grid">
        <span>Dato</span>
        <span>Llegó en el correo</span>
        <span>Maestro de proveedores</span>
      </div>
      {rows.map((r) => (
        <div key={r.label} className="grid gap-1 border-t px-3 py-2.5 text-body-sm first:border-t-0 sm:grid-cols-[10rem_1fr_1fr] sm:gap-3 sm:first:border-t">
          <span className="flex items-center gap-1.5 text-muted-foreground">
            {r.isMismatch ? (
              <XCircle aria-hidden className="size-4 text-danger" />
            ) : (
              <CheckCircle2 aria-hidden className="size-4 text-success" />
            )}
            {r.label}
            <span className="sr-only">{r.isMismatch ? ": no coincide" : ": coincide"}</span>
          </span>
          <span className={cn("break-all font-mono", r.isMismatch && "font-semibold text-danger")}>{r.received}</span>
          <span className="break-all font-mono">{r.master}</span>
        </div>
      ))}
    </div>
  );
}
