import { formatDate } from "@/shared/lib/format";
import { PageHeader } from "@/shared/ui/molecules/PageHeader";
import { StatTile } from "@/shared/ui/molecules/StatTile";

import { getSession } from "@/shared/lib/session";

import { fetchCoordinatorSummary, fetchWeeklyReport } from "../../api/deadline-queries";
import { CoordinatorSummary } from "../organisms/CoordinatorSummary";
import { DeadlineGroup } from "../organisms/DeadlineGroup";
import { PrintButton } from "../organisms/PrintButton";

export async function DeadlinesTemplate() {
  const session = await getSession();
  const isCoordinator = session?.role === "COORDINATOR";
  const [report, summary] = await Promise.all([
    fetchWeeklyReport(),
    isCoordinator ? fetchCoordinatorSummary() : Promise.resolve(null),
  ]);
  const urgent = [...report.overdue, ...report.thisWeek, ...report.nextWeek].filter((d) => d.isUrgent).length;
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={`Semana del ${formatDate(report.weekStart)} al ${formatDate(report.weekEnd)}`}
        title="Vencimientos"
        description="Derechos de petición, oficios y quejas con plazo, contados en días hábiles. Incluye lo que llegó pero aún no se ha radicado: el plazo corre desde que llega."
        actions={<PrintButton />}
      />
      {summary ? <CoordinatorSummary {...summary} /> : null}
      <section aria-label="Resumen" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Vencidos" value={report.overdue.length} tone="danger" />
        <StatTile label="Esta semana" value={report.thisWeek.length} tone="warning" />
        <StatTile label="Próxima semana" value={report.nextWeek.length} tone="info" />
        <StatTile label="Urgentes" value={urgent} tone="danger" hint={`${report.notFiledYet} aún sin radicar`} />
      </section>
      <div className="grid gap-8 xl:grid-cols-2">
        <div className="space-y-8">
          <DeadlineGroup title="Vencidos" items={report.overdue} empty="Nada vencido." />
          <DeadlineGroup title="Vencen esta semana" items={report.thisWeek} empty="Nada vence esta semana." />
        </div>
        <DeadlineGroup title="Vencen la próxima semana" items={report.nextWeek} empty="Nada vence la próxima semana." />
      </div>
    </div>
  );
}
