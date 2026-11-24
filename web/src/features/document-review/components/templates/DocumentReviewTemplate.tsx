import { ArrowLeft, FileQuestion } from "lucide-react";
import Link from "next/link";

import { presentationLabel } from "@/shared/i18n/es";
import { formatDateTime } from "@/shared/lib/format";
import { fetchCaseToday } from "@/shared/lib/case-date";
import { getSession } from "@/shared/lib/session";
import { Eyebrow } from "@/shared/ui/atoms/Eyebrow";
import { DocumentStatusBadge } from "@/shared/ui/molecules/DocumentStatusBadge";
import { UrgentBadge } from "@/shared/ui/molecules/UrgentBadge";
import { EmptyState } from "@/shared/ui/molecules/EmptyState";
import { StatusBadge } from "@/shared/ui/molecules/StatusBadge";
import { Button } from "@/shared/ui/primitives/button";

import { fetchDocument, fetchNextPendingId } from "../../api/document-queries";
import { AuditTimeline } from "../molecules/AuditTimeline";
import { DecisionSummary } from "../molecules/DecisionSummary";
import { FieldList } from "../molecules/FieldList";
import { ReasonList } from "../molecules/ReasonList";
import { ReviewActions } from "../organisms/ReviewActions";
import { SourceViewer } from "../organisms/SourceViewer";

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border bg-card p-4 shadow-xs sm:p-5">
      <h2 className="mb-3 text-headline-sm">{title}</h2>
      {children}
    </section>
  );
}

export async function DocumentReviewTemplate({ params }: { params: Promise<{ id: string }> }) {
  const { id: rawId } = await params;
  const id = decodeURIComponent(rawId);
  const [doc, session, nextId, today] = await Promise.all([
    fetchDocument(id),
    getSession(),
    fetchNextPendingId(id),
    fetchCaseToday(),
  ]);

  if (!doc) {
    return (
      <EmptyState
        icon={FileQuestion}
        title="Documento no encontrado"
        action={
          <Button asChild variant="outline">
            <Link href="/inbox">Volver a la bandeja</Link>
          </Button>
        }
      />
    );
  }

  const isOpen = doc.status === "READY" || doc.status === "NEEDS_REVIEW";
  const canAct = isOpen && session?.role === "CLERK";

  return (
    <div className="space-y-6">
      <Link href="/inbox" className="inline-flex min-h-11 items-center gap-1.5 text-label-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft aria-hidden className="size-4" /> Bandeja
      </Link>

      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <DocumentStatusBadge status={doc.status} action={doc.decision.action} />
          {doc.decision.isUrgent ? <UrgentBadge /> : null}
          {doc.decision.isLate ? <StatusBadge tone="warning" label={presentationLabel.late} /> : null}
          {doc.wasCorrected ? <StatusBadge tone="info" label="Corregido por una persona" /> : null}
          {doc.filingNumber ? <span className="font-mono text-body-sm font-normal">{doc.filingNumber}</span> : null}
        </div>
        <div>
          <Eyebrow>{doc.documentName}</Eyebrow>
          <h1 className="text-headline-lg">{doc.subject}</h1>
          <p className="text-body-sm text-muted-foreground">
            {doc.senderName} &lt;{doc.sender}&gt; · recibido {formatDateTime(doc.receivedAt)}
          </p>
        </div>
        {canAct ? (
          <ReviewActions documentId={doc.id} decision={doc.decision} notes={doc.notes} needsReview={doc.needsReview} nextId={nextId} today={today} />
        ) : null}
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
        <div className="order-2 min-w-0 lg:order-1">
          <SourceViewer
            documentId={doc.id}
            documentName={doc.documentName}
            isEmailBody={doc.isEmailBody}
            extractionMethod={doc.extractionMethod}
            ocrConfidence={doc.ocrConfidence}
            text={doc.text}
            emailBody={doc.emailBody}
          />
        </div>
        <div className="order-1 min-w-0 space-y-4 lg:order-2">
          <Panel title={doc.wasCorrected ? "Decisión (corregida)" : "Propuesta del sistema"}>
            <DecisionSummary decision={doc.decision} />
            {doc.wasCorrected ? (
              <details className="mt-3 text-body-sm">
                <summary className="cursor-pointer text-muted-foreground">Ver la propuesta original</summary>
                <div className="mt-2 opacity-80">
                  <DecisionSummary decision={doc.proposal} />
                </div>
              </details>
            ) : null}
          </Panel>
          <Panel title="Por qué">
            <ReasonList reasons={doc.reasons} />
          </Panel>
          <Panel title="Datos extraídos">
            <FieldList fields={doc.fields} />
          </Panel>
          {doc.audit.length ? (
            <Panel title="Historial">
              <AuditTimeline events={doc.audit} />
            </Panel>
          ) : null}
        </div>
      </div>
    </div>
  );
}
