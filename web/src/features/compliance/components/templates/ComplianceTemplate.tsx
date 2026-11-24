import { ShieldCheck } from "lucide-react";

import { documentTypeLabel } from "@/shared/i18n/es";
import { formatDate } from "@/shared/lib/format";
import { fetchCaseToday } from "@/shared/lib/case-date";
import { getSession } from "@/shared/lib/session";
import { DatePicker } from "@/shared/ui/molecules/DatePicker";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { Button } from "@/shared/ui/primitives/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/shared/ui/primitives/table";

import { fetchComplianceData } from "../../api/compliance-queries";
import { dispositionLabel, parsePreviewDate } from "../../model/labels";
import { DisposeButton } from "../organisms/DisposeButton";
import { SubjectRequestForm } from "../organisms/SubjectRequestForm";

const years = (n: number) => `${n} ${n === 1 ? "año" : "años"}`;

function Section({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-headline-md">{title}</h2>
        <p className="max-w-3xl text-body-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  );
}

export async function ComplianceTemplate({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const previewDate = parsePreviewDate((await searchParams).on);
  const [{ schedule, due, inventory }, session, today] = await Promise.all([
    fetchComplianceData(previewDate),
    getSession(),
    fetchCaseToday(),
  ]);
  const isCoordinator = session?.role === "COORDINATOR";
  return (
    <div className="space-y-10">
      <PageHeader
        eyebrow="Coordinación"
        title="Cumplimiento"
        description="Retención documental (Ley 594 de 2000) y protección de datos personales (Ley 1581 de 2012)."
      />

      <Section
        title="Tabla de retención documental"
        description="Propuesta inicial por tipo documental; debe aprobarla el Comité Interno de Archivo. Los años cuentan desde el cierre del año en que se recibió."
      >
        <div className="overflow-x-auto rounded-xl border bg-card shadow-xs">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Tipo documental</TableHead>
                <TableHead className="text-right">Gestión</TableHead>
                <TableHead className="text-right">Central</TableHead>
                <TableHead>Disposición final</TableHead>
                <TableHead>Fundamento</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedule.map((r) => (
                <TableRow key={r.document_type}>
                  <TableCell>{documentTypeLabel[r.document_type]}</TableCell>
                  <TableCell className="text-right tabular">{years(r.office_years)}</TableCell>
                  <TableCell className="text-right tabular">{years(r.central_years)}</TableCell>
                  <TableCell>{dispositionLabel[r.disposition]}</TableCell>
                  <TableCell className="min-w-64 whitespace-normal text-muted-foreground">{r.basis}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Section>

      <Section
        title="Documentos que cumplieron su retención"
        description="Nada se elimina antes de tiempo ni sin acta. Puede revisar qué vencerá en una fecha futura."
      >
        <form action="/compliance" className="flex flex-wrap items-end gap-2">
          <div className="space-y-1.5 text-label-sm">
            <label htmlFor="retention-on" className="block">
              Ver a la fecha
            </label>
            <DatePicker id="retention-on" name="on" defaultValue={previewDate ?? ""} today={today} className="w-56" />
          </div>
          <Button type="submit" variant="outline">
            Consultar
          </Button>
        </form>
        {due.total === 0 ? (
          <p className="flex items-center gap-2 rounded-xl border border-dashed p-4 text-body-sm text-muted-foreground">
            <ShieldCheck aria-hidden className="size-4 text-success" />
            Ningún documento ha cumplido su tiempo de retención{previewDate ? ` al ${formatDate(previewDate)}` : ""}.
          </p>
        ) : (
          <ul className="divide-y rounded-xl border bg-card">
            {due.items.map((v) => (
              <li key={v.filing_number} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-body-sm">
                <span>
                  <span className="font-mono">{v.filing_number}</span> · {documentTypeLabel[v.document_type]} · retención hasta{" "}
                  {formatDate(v.retention_ends)} · {dispositionLabel[v.disposition]}
                </span>
                {isCoordinator && v.disposition === "DESTROY" && !previewDate ? <DisposeButton filingNumber={v.filing_number} /> : null}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        title="Datos personales"
        description="Qué datos guarda Docket, para qué, con qué base legal, quién los ve y cuánto tiempo."
      >
        <div className="overflow-x-auto rounded-xl border bg-card shadow-xs">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Dato</TableHead>
                <TableHead>Titulares</TableHead>
                <TableHead>Finalidad y base legal</TableHead>
                <TableHead>Quién lo ve</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {inventory.items.map((i) => (
                <TableRow key={i.data}>
                  <TableCell className="min-w-48 whitespace-normal">{i.data}</TableCell>
                  <TableCell className="min-w-40 whitespace-normal text-muted-foreground">{i.subjects}</TableCell>
                  <TableCell className="min-w-64 whitespace-normal">
                    {i.purpose}
                    <span className="block text-caption text-muted-foreground">{i.legal_basis}</span>
                  </TableCell>
                  <TableCell className="min-w-40 whitespace-normal text-muted-foreground">{i.access}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <ul className="grid gap-2 text-body-sm md:grid-cols-2">
          {inventory.safeguards.map((s) => (
            <li key={s} className="flex gap-2 rounded-lg bg-success-soft px-3 py-2 text-success-soft-foreground">
              <ShieldCheck aria-hidden className="mt-0.5 size-4 shrink-0" /> {s}
            </li>
          ))}
        </ul>
        {isCoordinator ? (
          <div className="space-y-2">
            <h3 className="text-headline-sm">Solicitud de un titular</h3>
            <SubjectRequestForm />
          </div>
        ) : null}
      </Section>
    </div>
  );
}
