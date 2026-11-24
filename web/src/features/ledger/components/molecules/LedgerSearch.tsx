import { Search } from "lucide-react";

import { departmentLabel, documentTypeLabel } from "@/shared/i18n/es";
import { DEPARTMENTS, DOCUMENT_TYPES } from "@/shared/lib/api-types";
import { FilterSelect } from "@/shared/ui/molecules/FilterSelect";
import { Button } from "@/shared/ui/primitives/button";
import { Input } from "@/shared/ui/primitives/input";

import type { LedgerQueryView } from "../../model/types";

const DEPARTMENT_OPTIONS = DEPARTMENTS.filter((d) => d !== "SENDER").map((d) => ({ value: d, label: departmentLabel[d] }));
const TYPE_OPTIONS = DOCUMENT_TYPES.map((t) => ({ value: t, label: documentTypeLabel[t] }));

/** Plain GET form: filters live in the URL, so a search can be shared or bookmarked. */
export function LedgerSearch({ query }: { query: LedgerQueryView }) {
  return (
    <form role="search" action="/ledger" className="grid gap-2 md:grid-cols-[1fr_minmax(12rem,auto)_minmax(12rem,auto)_auto]">
      <label className="sr-only" htmlFor="ledger-q">
        Buscar en el libro
      </label>
      <Input id="ledger-q" name="q" defaultValue={query.q} placeholder="Radicado, remitente, NIT, asunto o número" className="h-11" />
      <FilterSelect
        id="ledger-department"
        name="department"
        label="Dependencia"
        allLabel="Todas las dependencias"
        options={DEPARTMENT_OPTIONS}
        defaultValue={query.department}
      />
      <FilterSelect
        id="ledger-type"
        name="type"
        label="Tipo documental"
        allLabel="Todos los tipos"
        options={TYPE_OPTIONS}
        defaultValue={query.documentType}
      />
      <Button type="submit" className="h-11">
        <Search aria-hidden /> Buscar
      </Button>
    </form>
  );
}
