import { Copy, Download } from "lucide-react";

import { plural } from "@/shared/lib/format";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { Pagination } from "@/shared/ui/molecules/Pagination";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/primitives/alert";
import { Button } from "@/shared/ui/primitives/button";

import { fetchLedgerDuplicates, fetchLedgerPage, fetchLedgerSyncState } from "../../api/ledger-queries";
import { LedgerSyncStatus } from "../organisms/LedgerSyncStatus";
import { ledgerPageHref, parseLedgerOffset, parseLedgerQuery } from "../../model/mappers";
import { LedgerSearch } from "../molecules/LedgerSearch";
import { LedgerTable } from "../organisms/LedgerTable";

interface LedgerTemplateProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export async function LedgerTemplate({ searchParams }: LedgerTemplateProps) {
  const params = await searchParams;
  const query = parseLedgerQuery(params);
  const [page, duplicates, syncState] = await Promise.all([
    fetchLedgerPage(query, parseLedgerOffset(params)),
    fetchLedgerDuplicates(),
    fetchLedgerSyncState(),
  ]);
  const entries = page.items;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Libro de radicación 2026"
        title="Libro"
        description="El mismo libro en Excel que consultan Contabilidad y Jurídica, con los radicados nuevos al final."
        actions={
          <Button asChild variant="outline" className="h-11">
            <a href="/files/ledger" download>
              <Download aria-hidden /> Descargar Excel
            </a>
          </Button>
        }
      />
      {duplicates.length ? (
        <Alert>
          <Copy aria-hidden />
          <AlertTitle>Posibles facturas duplicadas en el libro histórico</AlertTitle>
          <AlertDescription>
            {duplicates.map((group) => group.join(" y ")).join("; ")}: mismo proveedor y mismo número. Conviene que
            Contabilidad verifique que no se pagaron dos veces.
          </AlertDescription>
        </Alert>
      ) : null}
      <LedgerSyncStatus state={syncState} />
      <LedgerSearch query={query} />
      <p className="text-caption text-muted-foreground">{plural(page.total, "registro", "registros")}</p>
      <LedgerTable entries={entries} />
      <Pagination
        total={page.total}
        limit={page.limit}
        offset={page.offset}
        hrefFor={(offset) => ledgerPageHref(query, offset)}
        label="Páginas del libro"
      />
    </div>
  );
}
