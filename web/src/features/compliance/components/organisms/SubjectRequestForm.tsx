"use client";

import { Loader2, Search } from "lucide-react";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { describeError } from "@/shared/i18n/es";
import type { SubjectReportResponse } from "@/shared/lib/api-types";
import { formatDate } from "@/shared/lib/format";
import { Button } from "@/shared/ui/primitives/button";
import { Input } from "@/shared/ui/primitives/input";
import { Label } from "@/shared/ui/primitives/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/primitives/select";

import { subjectRequestAction } from "../../api/compliance-actions";
import { matchFieldLabel } from "../../model/labels";

export function SubjectRequestForm() {
  const [identifier, setIdentifier] = useState("");
  const [kind, setKind] = useState<"INQUIRY" | "CLAIM">("INQUIRY");
  const [report, setReport] = useState<SubjectReportResponse | null>(null);
  const [pending, startTransition] = useTransition();
  const search = (e: React.FormEvent) => {
    e.preventDefault();
    startTransition(async () => {
      const result = await subjectRequestAction(identifier, kind);
      if (!result.ok) return void toast.error(describeError(result.code));
      setReport(result.data);
    });
  };
  return (
    <div className="space-y-4">
      <form onSubmit={search} className="grid gap-3 md:grid-cols-[1fr_minmax(14rem,auto)_auto] md:items-end">
        <div className="space-y-1.5">
          <Label htmlFor="subject-id">Cédula o correo del titular</Label>
          <Input id="subject-id" value={identifier} onChange={(e) => setIdentifier(e.target.value)} autoComplete="off" className="h-11" />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="subject-kind">Tipo de solicitud</Label>
          <Select value={kind} onValueChange={(v) => setKind(v as "INQUIRY" | "CLAIM")}>
            <SelectTrigger id="subject-kind">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="INQUIRY" description="Responder en 10 días hábiles">
                Consulta (art. 14)
              </SelectItem>
              <SelectItem value="CLAIM" description="Corrección o supresión: 15 días hábiles">
                Reclamo (art. 15)
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Button type="submit" disabled={pending || identifier.trim().length < 3}>
          {pending ? <Loader2 aria-hidden className="animate-spin" /> : <Search aria-hidden />} Buscar
        </Button>
      </form>
      {report ? (
        <div className="space-y-2 rounded-xl border bg-card p-4" aria-live="polite">
          <p className="text-body-sm">
            Titular <span className="font-mono">{report.identifier_masked}</span>: {report.matches.length} registro(s). Responder a más
            tardar el <b>{formatDate(report.response_due)}</b>.
          </p>
          {report.matches.length ? (
            <ul className="divide-y text-body-sm">
              {report.matches.map((m) => (
                <li key={`${m.where}-${m.reference}`} className="flex flex-wrap justify-between gap-2 py-2">
                  <span className="font-mono">{m.reference}</span>
                  <span className="text-muted-foreground">
                    {m.where === "LEDGER" ? "Libro" : "Bandeja"} · {m.fields.map((f) => matchFieldLabel[f] ?? f).join(", ")} ·{" "}
                    {formatDate(m.received_date)}
                    {m.content_available ? "" : " · contenido eliminado"}
                  </span>
                </li>
              ))}
            </ul>
          ) : null}
          <p className="text-caption text-muted-foreground">La búsqueda queda auditada con el identificador enmascarado.</p>
        </div>
      ) : null}
    </div>
  );
}
