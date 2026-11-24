import { getSession } from "@/shared/lib/session";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { Pagination } from "@/shared/ui/molecules/Pagination";
import { StatTile } from "@/shared/ui/molecules/StatTile";

import { fetchHeldInInbox, fetchInboxPage, fetchInboxSummary } from "../../api/inbox-queries";
import { parseFilter, parseOffset, sortForWork } from "../../model/mappers";
import { filterCounts } from "../../model/types";
import { InboxFilters } from "../molecules/InboxFilters";
import { InboxList } from "../organisms/InboxList";
import { InboxToolbar } from "../organisms/InboxToolbar";

interface InboxTemplateProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export async function InboxTemplate({ searchParams }: InboxTemplateProps) {
  const params = await searchParams;
  const filter = parseFilter(params.filter);
  const offset = parseOffset(params.offset);
  const [page, summary, held, session] = await Promise.all([
    fetchInboxPage(filter, offset),
    fetchInboxSummary(),
    fetchHeldInInbox(),
    getSession(),
  ]);
  const counts = filterCounts(summary);
  const isClerk = session?.role === "CLERK";
  const hrefFor = (o: number) => `/inbox?${new URLSearchParams({ filter, offset: String(o) })}`;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Radicación"
        title="Bandeja"
        description="El sistema lee cada correo y propone qué es, a dónde va y cuándo vence. Usted confirma; nada sale sin su aprobación."
        actions={isClerk ? <InboxToolbar readyCount={counts.ready} /> : null}
      />
      <section aria-label="Resumen" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Por revisar" value={counts.review} tone="warning" hint="Decide una persona" />
        <StatTile label="Listos" value={counts.ready} tone="success" hint="Solo confirmar" />
        <StatTile label="Retenidas" value={held} tone="danger" hint="Verificar con el proveedor" />
        <StatTile label="Cerrados" value={counts.approved} tone="primary" hint="Aprobados o descartados" />
      </section>
      {isClerk ? null : (
        <p role="note" className="rounded-xl border border-dashed bg-card/60 px-4 py-3 text-body-sm text-muted-foreground">
          Vista de supervisión: puede revisar cada propuesta, pero radicar, corregir y aprobar le corresponde a Radicación.
        </p>
      )}
      <InboxFilters active={filter} counts={counts} />
      <InboxList items={sortForWork(page.items)} />
      <Pagination total={page.total} limit={page.limit} offset={page.offset} hrefFor={hrefFor} label="Páginas de la bandeja" />
    </div>
  );
}
