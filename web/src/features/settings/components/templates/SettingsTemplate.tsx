import { Bot, ShieldCheck } from "lucide-react";

import { departmentLabel } from "@/shared/i18n/es";
import { formatDateTime } from "@/shared/lib/format";
import { getSession } from "@/shared/lib/session";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { StatusBadge } from "@/shared/ui/molecules/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/primitives/table";

import { fetchSettingsData, fetchSystemStatus } from "../../api/settings-queries";
import { OutboxMessageCard } from "../molecules/OutboxMessageCard";
import { SupplierMasterUpload } from "../organisms/SupplierMasterUpload";

const CHECK_LABEL: Record<string, string> = {
  database: "Base de datos",
  ledger_template: "Libro de radicación (Excel)",
  ocr: "OCR para escaneados",
  import_worker: "Procesador de la cola",
};
const CHECK_VALUE: Record<string, string> = { OK: "Funciona", DEGRADED: "Degradado", DOWN: "Caído", MISSING: "Falta" };

function Section({ title, description, actions, children }: { title: string; description?: string; actions?: React.ReactNode; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-headline-md">{title}</h2>
          {description ? <p className="text-body-sm text-muted-foreground">{description}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

export async function SettingsTemplate() {
  const [{ suppliers, departments, outbox, isLlmEnabled }, status, session] = await Promise.all([
    fetchSettingsData(),
    fetchSystemStatus(),
    getSession(),
  ]);
  return (
    <div className="space-y-10">
      <PageHeader eyebrow="Configuración" title="Ajustes" description="Datos maestros, reglas de reenvío y los correos que el sistema generó." />

      <Section title="Estado del sistema" description="Lo mismo que vigila el monitoreo (métricas en /metrics, verificación en /api/ready).">
        <div className="grid gap-3 md:grid-cols-2">
          <ul className="divide-y rounded-xl border bg-card px-4 text-body-sm shadow-xs">
            {Object.entries(status.checks).map(([check, value]) => (
              <li key={check} className="flex items-center justify-between py-2.5">
                <span>{CHECK_LABEL[check] ?? "Otro componente"}</span>
                <StatusBadge tone={value === "OK" ? "success" : value === "DEGRADED" ? "warning" : "danger"} label={CHECK_VALUE[value] ?? "Sin dato"} />
              </li>
            ))}
          </ul>
          <div className="rounded-xl border bg-card p-4 text-body-sm shadow-xs">
            <p className="text-label-md">Cola de importación</p>
            <p className="mt-1 text-muted-foreground tabular">
              {status.queue.QUEUED ?? 0} en cola · {status.queue.RUNNING ?? 0} procesando · {status.queue.DONE ?? 0} terminadas ·{" "}
              {status.queue.FAILED ?? 0} fallidas
            </p>
            {status.jobs[0] ? (
              <p className="mt-2 text-caption text-muted-foreground">
                Última: {formatDateTime(status.jobs[0].created_at)} · {status.jobs[0].result?.imported.length ?? 0} documentos nuevos
              </p>
            ) : null}
          </div>
        </div>
      </Section>

      <Section title="Asistente de IA">
        <div className="flex items-start gap-3 rounded-xl border bg-card p-4 shadow-xs">
          {isLlmEnabled ? <Bot aria-hidden className="mt-0.5 size-5 text-warning" /> : <ShieldCheck aria-hidden className="mt-0.5 size-5 text-success" />}
          <div className="space-y-1 text-body-sm">
            <StatusBadge tone={isLlmEnabled ? "warning" : "success"} label={isLlmEnabled ? "Activo" : "Apagado"} />
            <p className="text-muted-foreground">
              {isLlmEnabled
                ? "Solo se consulta en textos ambiguos, con datos personales enmascarados, y su sugerencia siempre pasa a revisión."
                : "Todo se decide con reglas y OCR locales: ningún documento sale de TAC. Sistemas puede activarlo cuando lo apruebe."}
            </p>
          </div>
        </div>
      </Section>

      <Section
        title="Maestro de proveedores"
        description="Exportado del ERP por Compras. Se usa para validar NIT, cuenta bancaria y correo de cada factura."
        actions={session?.role === "CLERK" ? <SupplierMasterUpload /> : null}
      >
        <div className="overflow-x-auto rounded-xl border bg-card shadow-xs">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Proveedor</TableHead>
                <TableHead>NIT</TableHead>
                <TableHead>Correo de facturación</TableHead>
                <TableHead>Cuenta</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {suppliers.map((s) => (
                <TableRow key={s.nit}>
                  <TableCell className="min-w-56">{s.name}</TableCell>
                  <TableCell className="font-mono text-body-sm font-normal">{s.nit}</TableCell>
                  <TableCell>{s.billing_email}</TableCell>
                  <TableCell className="font-mono text-body-sm font-normal">{s.bank} · {s.account_number}</TableCell>
                  <TableCell>
                    <StatusBadge tone={s.is_active ? "success" : "muted"} label={s.is_active ? "Activo" : "Inactivo"} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Section>

      <Section title="Dependencias" description="A dónde se reenvía cada tipo de documento.">
        <ul className="grid gap-3 md:grid-cols-2">
          {departments.map((d) => (
            <li key={d.code} className="rounded-xl border bg-card p-4 shadow-xs">
              <p className="text-label-md">{departmentLabel[d.code]}</p>
              <p className="text-caption text-muted-foreground">{d.email}</p>
              <p className="mt-1 text-body-sm">{d.receives}</p>
            </li>
          ))}
        </ul>
      </Section>

      <Section
        title="Bandeja de salida (simulada)"
        description="Los correos que el sistema enviaría al aprobar. En esta versión no se envía nada de verdad."
      >
        {outbox.length ? (
          <ul className="space-y-2">
            {outbox.map((m, i) => (
              <OutboxMessageCard key={`${m.document_id}-${i}`} message={m} />
            ))}
          </ul>
        ) : (
          <p className="rounded-xl border border-dashed p-4 text-body-sm text-muted-foreground">Aún no hay correos generados.</p>
        )}
      </Section>
    </div>
  );
}
