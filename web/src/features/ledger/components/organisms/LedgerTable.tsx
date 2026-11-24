import { Ban, BookOpen, Check, CheckCheck, Clock, ShieldAlert, type LucideIcon } from "lucide-react";

import { departmentLabel, documentTypeLabel, ledgerStatusLabel } from "@/shared/i18n/es";
import { cn } from "@/shared/lib/cn";
import { formatDate, formatDateNumeric, formatMoney } from "@/shared/lib/format";
import { UrgentBadge } from "@/shared/ui/molecules/UrgentBadge";
import { EmptyState } from "@/shared/ui/molecules/EmptyState";
import { StatusBadge, type BadgeTone } from "@/shared/ui/molecules/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/primitives/table";

import type { LedgerEntryView } from "../../model/types";

const STATUS_TONE: Record<LedgerEntryView["status"], BadgeTone> = { DELIVERED: "muted", IN_PROGRESS: "info", ON_HOLD: "danger", REJECTED: "danger", CLOSED: "success" };
const STATUS_ICON: Record<LedgerEntryView["status"], LucideIcon> = { DELIVERED: Check, IN_PROGRESS: Clock, ON_HOLD: ShieldAlert, REJECTED: Ban, CLOSED: CheckCheck };

export function LedgerTable({ entries }: { entries: LedgerEntryView[] }) {
  if (!entries.length) return <EmptyState icon={BookOpen} title="Sin resultados" description="Pruebe con otra búsqueda." />;
  return (
    <>
      {/* Phones: cards */}
      <ul className="space-y-2 md:hidden">
        {entries.map((e) => (
          <li key={e.filingNumber} className={cn("rounded-xl border bg-card p-4 shadow-xs", e.isNew && "border-l-4 border-l-primary")}>
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono text-body-sm font-normal">{e.filingNumber}</span>
              <StatusBadge tone={STATUS_TONE[e.status]} label={ledgerStatusLabel[e.status]} icon={STATUS_ICON[e.status]} />
            </div>
            <p className="mt-1 text-label-md">{e.subject}</p>
            <p className="text-caption text-muted-foreground">
              {e.sender} · {documentTypeLabel[e.documentType]} → {departmentLabel[e.department]}
            </p>
            <p className="mt-1 text-caption tabular text-muted-foreground">
              {formatDate(e.receivedDate)}
              {e.dueDate ? ` · vence ${formatDate(e.dueDate)}` : ""}
              {e.totalAmount ? ` · ${formatMoney(e.totalAmount)}` : ""}
            </p>
          </li>
        ))}
      </ul>
      {/* Tablet and desktop: the ledger as Accounting knows it */}
      <div className="hidden overflow-hidden rounded-xl border bg-card shadow-xs md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Radicado</TableHead>
              <TableHead>Recibido</TableHead>
              <TableHead>Remitente</TableHead>
              <TableHead>Asunto y tipo</TableHead>
              <TableHead className="text-right">Valor</TableHead>
              <TableHead>Dependencia</TableHead>
              <TableHead>Vence</TableHead>
              <TableHead>Estado</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.map((e) => (
              <TableRow key={e.filingNumber} className={cn(e.isNew && "bg-primary-soft/40")}>
                <TableCell className="font-mono text-body-sm font-normal whitespace-nowrap">{e.filingNumber}</TableCell>
                <TableCell className="tabular">{formatDateNumeric(e.receivedDate)}</TableCell>
                <TableCell className="min-w-40 whitespace-normal">{e.sender}</TableCell>
                <TableCell className="min-w-48 whitespace-normal" title={e.notes ? `${e.subject} — ${e.notes}` : e.subject}>
                  <span className="block">{e.subject}</span>
                  <span className="block text-caption text-muted-foreground">{documentTypeLabel[e.documentType]}</span>
                </TableCell>
                <TableCell className="text-right tabular">{formatMoney(e.totalAmount)}</TableCell>
                <TableCell>{departmentLabel[e.department]}</TableCell>
                <TableCell className="tabular">
                  <span className="flex items-center gap-1.5">
                    {formatDateNumeric(e.dueDate)}
                    {e.isUrgent ? <UrgentBadge /> : null}
                  </span>
                </TableCell>
                <TableCell>
                  <StatusBadge tone={STATUS_TONE[e.status]} label={ledgerStatusLabel[e.status]} icon={STATUS_ICON[e.status]} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </>
  );
}
