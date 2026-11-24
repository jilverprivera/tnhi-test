import { ExternalLink } from "lucide-react";
import Link from "next/link";

import { departmentLabel, verificationStateLabel } from "@/shared/i18n/es";
import { cn } from "@/shared/lib/cn";
import { formatDateTime, formatMoney } from "@/shared/lib/format";
import { StatusBadge, type BadgeTone } from "@/shared/ui/molecules/StatusBadge";

import type { HeldInvoiceView } from "../../model/types";
import { ComparisonTable } from "../molecules/ComparisonTable";
import { VerifyActions } from "./VerifyActions";

const STATE_TONE: Record<HeldInvoiceView["state"], BadgeTone> = {
  AWAITING_VERIFICATION: "danger",
  PENDING_CLERK_APPROVAL: "warning",
  RELEASED: "success",
  REJECTED: "muted",
};

export function HeldInvoiceCard({ invoice, canResolve }: { invoice: HeldInvoiceView; canResolve: boolean }) {
  const isAwaiting = invoice.state === "AWAITING_VERIFICATION";
  return (
    <article
      aria-labelledby={`held-${invoice.id}`}
      className={cn("space-y-4 rounded-xl border bg-card p-4 shadow-xs sm:p-5", isAwaiting && "border-l-4 border-l-danger")}
    >
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge tone={STATE_TONE[invoice.state]} label={verificationStateLabel[invoice.state]} />
            {invoice.filingNumber ? <span className="font-mono text-body-sm">{invoice.filingNumber}</span> : null}
          </div>
          <h2 id={`held-${invoice.id}`} className="text-headline-sm">
            {invoice.supplierName} · Factura {invoice.invoiceNumber}
          </h2>
          <p className="text-body-sm text-muted-foreground">
            {formatMoney(invoice.totalAmount)} · {invoice.purchaseOrder || "Sin OC"} · recibida {formatDateTime(invoice.receivedAt)}
          </p>
        </div>
        <Link
          href={`/documents/${encodeURIComponent(invoice.id)}`}
          className="inline-flex min-h-11 items-center gap-1.5 text-label-sm text-primary"
        >
          <ExternalLink aria-hidden className="size-4" /> Ver documento
        </Link>
      </header>

      {invoice.reasons.length ? (
        <ul className="space-y-1 text-body-sm text-danger">
          {invoice.reasons.map((r) => (
            <li key={r}>• {r}</li>
          ))}
        </ul>
      ) : null}

      <ComparisonTable rows={invoice.comparisons} />

      <p className="text-body-sm">
        <span className="text-muted-foreground">Llame al contacto del maestro, no al del correo: </span>
        {invoice.masterContact}
      </p>

      {invoice.resolution ? (
        <p className="rounded-lg bg-muted p-3 text-body-sm">
          <span className="font-semibold">{verificationStateLabel[invoice.resolution.outcome]}</span> ·{" "}
          {formatDateTime(invoice.resolution.at)} · {invoice.resolution.note}
        </p>
      ) : null}

      {isAwaiting && canResolve ? (
        <div className="flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-caption text-muted-foreground">
            Si la libera, sigue hacia {departmentLabel[invoice.releaseDepartment]}.
          </p>
          <VerifyActions documentId={invoice.id} filingNumber={invoice.filingNumber} releaseDepartment={invoice.releaseDepartment} />
        </div>
      ) : null}
      {invoice.state === "PENDING_CLERK_APPROVAL" ? (
        <p className="text-caption text-muted-foreground">Radicación debe aprobarla primero para que quede radicada y retenida.</p>
      ) : null}
    </article>
  );
}
