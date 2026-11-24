import { ShieldCheck } from "lucide-react";

import { getSession } from "@/shared/lib/session";
import { EmptyState } from "@/shared/ui/molecules/EmptyState";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { StatTile } from "@/shared/ui/molecules/StatTile";

import { fetchHeldInvoices } from "../../api/verification-queries";
import { splitByState } from "../../model/mappers";
import type { HeldInvoiceView } from "../../model/types";
import { HeldInvoiceCard } from "../organisms/HeldInvoiceCard";

function Group({ title, items, canResolve }: { title: string; items: HeldInvoiceView[]; canResolve: boolean }) {
  if (!items.length) return null;
  return (
    <section className="space-y-3">
      <h2 className="text-headline-md">
        {title} <span className="text-muted-foreground tabular">({items.length})</span>
      </h2>
      {items.map((i) => (
        <HeldInvoiceCard key={i.id} invoice={i} canResolve={canResolve} />
      ))}
    </section>
  );
}

export async function VerificationsTemplate() {
  const [items, session] = await Promise.all([fetchHeldInvoices(), getSession()]);
  const { awaiting, withClerk, resolved } = splitByState(items);
  const canResolve = session?.role === "COORDINATOR";
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Coordinación"
        title="Por verificar"
        description="Facturas retenidas por posible fraude: la cuenta o el remitente no coinciden con el maestro. Verifique por teléfono con el proveedor antes de liberarlas."
      />
      <section aria-label="Resumen" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Por verificar" value={awaiting.length} tone="danger" hint="Esperan su llamada" />
        <StatTile label="En bandeja de radicación" value={withClerk.length} tone="warning" hint="Aún sin radicar" />
        <StatTile label="Liberadas" value={resolved.filter((r) => r.state === "RELEASED").length} tone="success" />
        <StatTile label="Fraudes confirmados" value={resolved.filter((r) => r.state === "REJECTED").length} tone="muted" />
      </section>
      {items.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="No hay facturas retenidas" description="Cuando una cuenta o un remitente no coincidan con el maestro, aparecerán aquí." />
      ) : (
        <>
          <Group title="Esperan su verificación" items={awaiting} canResolve={canResolve} />
          <Group title="Aún en la bandeja de radicación" items={withClerk} canResolve={false} />
          <Group title="Resueltas" items={resolved} canResolve={false} />
        </>
      )}
    </div>
  );
}
