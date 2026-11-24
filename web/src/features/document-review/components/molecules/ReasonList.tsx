import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { cn } from "@/shared/lib/cn";

import type { ReasonView } from "../../model/types";

/** The "why" behind the proposal. Blocking reasons first: those are what a person must decide. */
export function ReasonList({ reasons }: { reasons: ReasonView[] }) {
  return (
    <ul className="space-y-2">
      {reasons.map((r) => (
        <li
          key={r.code}
          className={cn(
            "flex gap-2.5 rounded-lg px-3 py-2 text-body-sm",
            r.isBlocking ? "bg-warning-soft text-warning-soft-foreground" : "bg-muted text-foreground-secondary",
          )}
        >
          {r.isBlocking ? (
            <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" />
          ) : (
            <CheckCircle2 aria-hidden className="mt-0.5 size-4 shrink-0 text-success" />
          )}
          <span>
            <span className="sr-only">{r.isBlocking ? "Requiere decisión: " : "Regla aplicada: "}</span>
            {r.text}
          </span>
        </li>
      ))}
    </ul>
  );
}
