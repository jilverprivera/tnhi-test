import { ArrowRight, Inbox, ShieldAlert } from "lucide-react";
import Link from "next/link";

import { plural } from "@/shared/lib/format";

interface CoordinatorSummaryProps {
  awaitingVerification: number;
  heldInInbox: number;
  clerkBacklog: number;
  clerkNeedsReview: number;
}

/** The coordinator's control panel: what waits on her, and how the clerk's queue is doing. */
export function CoordinatorSummary(props: CoordinatorSummaryProps) {
  return (
    <section aria-label="Lo que requiere su atención" className="grid gap-3 md:grid-cols-2">
      <Link
        href="/verifications"
        className="group flex items-center gap-4 rounded-xl border border-l-4 border-l-danger bg-card p-4 shadow-xs transition-colors hover:bg-accent/50"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-full bg-danger-soft text-danger-soft-foreground">
          <ShieldAlert aria-hidden className="size-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-headline-sm">{plural(props.awaitingVerification, "factura por verificar", "facturas por verificar")}</span>
          <span className="block text-body-sm text-muted-foreground">
            Posible fraude: confirme por teléfono antes de liberar.
            {props.heldInInbox ? ` ${props.heldInInbox} más aún en la bandeja de radicación.` : ""}
          </span>
        </span>
        <ArrowRight aria-hidden className="size-5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </Link>
      <Link
        href="/inbox"
        className="group flex items-center gap-4 rounded-xl border bg-card p-4 shadow-xs transition-colors hover:bg-accent/50"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-full bg-primary-soft text-primary-soft-foreground">
          <Inbox aria-hidden className="size-5" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-headline-sm">{plural(props.clerkBacklog, "documento pendiente", "documentos pendientes")} en radicación</span>
          <span className="block text-body-sm text-muted-foreground">
            {props.clerkNeedsReview
              ? `${props.clerkNeedsReview} ${props.clerkNeedsReview === 1 ? "requiere" : "requieren"} decisión de una persona.`
              : "Nada atascado en revisión."}
          </span>
        </span>
        <ArrowRight aria-hidden className="size-5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
      </Link>
    </section>
  );
}
