"use client";

import { Check, Loader2, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { describeError } from "@/shared/i18n/es";
import { Button } from "@/shared/ui/primitives/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/ui/primitives/dialog";
import { Label } from "@/shared/ui/primitives/label";
import { Textarea } from "@/shared/ui/primitives/textarea";

import { approveDocumentAction, discardDocumentAction } from "../../api/document-actions";
import type { DecisionView } from "../../model/types";
import { CorrectionSheet } from "./CorrectionSheet";
import { EscalateHoldButton } from "./EscalateHoldButton";

interface ReviewActionsProps {
  documentId: string;
  decision: DecisionView;
  notes: string;
  needsReview: boolean;
  nextId: string | null;
  /** The case's "today" (from the API), used by the due-date picker. */
  today: string;
}

const APPROVE_LABEL: Record<DecisionView["action"], string> = {
  FILE: "Aprobar y radicar",
  HOLD_FOR_VERIFICATION: "Alertar a la Dra. Herrera",
  REPLY_WITH_EXISTING_NUMBER: "Aprobar respuesta",
  RETURN_TO_SENDER: "Aprobar devolución",
  DO_NOT_FILE: "Confirmar: no radicar",
};

export function ReviewActions({ documentId, decision, notes, needsReview, nextId, today }: ReviewActionsProps) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [reason, setReason] = useState("");
  const goNext = () => router.push(nextId ? `/documents/${encodeURIComponent(nextId)}` : "/inbox");

  const approve = () =>
    startTransition(async () => {
      const result = await approveDocumentAction(documentId);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success(result.data.filingNumber ? `Radicado ${result.data.filingNumber}` : "Aprobado", {
        description: "Quedó en el libro y en la bandeja de salida.",
      });
      goNext();
    });

  const discard = () =>
    startTransition(async () => {
      const result = await discardDocumentAction(documentId, reason);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success("Documento descartado.");
      goNext();
    });

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
      {decision.action === "HOLD_FOR_VERIFICATION" ? (
        <EscalateHoldButton documentId={documentId} onDone={goNext} />
      ) : (
        <Button className="h-11" onClick={approve} disabled={pending}>
          {pending ? <Loader2 aria-hidden className="animate-spin" /> : <Check aria-hidden />}
          {APPROVE_LABEL[decision.action]}
        </Button>
      )}
      <CorrectionSheet documentId={documentId} decision={decision} notes={notes} today={today} />
      <Dialog>
        <DialogTrigger asChild>
          <Button variant="ghost" className="h-11 text-danger">
            <Trash2 aria-hidden /> Descartar
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Descartar este documento?</DialogTitle>
            <DialogDescription>No se radica ni se reenvía. Queda registrado con el motivo.</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="discard-reason">Motivo</Label>
            <Textarea id="discard-reason" value={reason} onChange={(e) => setReason(e.target.value)} rows={3} />
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancelar</Button>
            </DialogClose>
            <Button variant="destructive" onClick={discard} disabled={pending || !reason.trim()}>
              Descartar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {needsReview ? (
        <p className="basis-full text-caption text-muted-foreground">
          {decision.action === "HOLD_FOR_VERIFICATION"
            ? "Posible fraude: no se aprueba. Alerte a la coordinadora para que lo verifique por teléfono."
            : "Al aprobar usted confirma que revisó los motivos marcados."}
        </p>
      ) : null}
    </div>
  );
}
