"use client";

import { Ban, Loader2, PhoneCall, ShieldCheck } from "lucide-react";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { departmentLabel, describeError } from "@/shared/i18n/es";
import type { Department } from "@/shared/lib/api-types";
import { Button } from "@/shared/ui/primitives/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/primitives/dialog";
import { Label } from "@/shared/ui/primitives/label";
import { Textarea } from "@/shared/ui/primitives/textarea";

import { resolveHoldAction, type VerificationOutcome } from "../../api/verification-actions";

interface VerifyActionsProps {
  documentId: string;
  filingNumber: string | null;
  releaseDepartment: Department;
}

const COPY: Record<VerificationOutcome, { title: string; description: string; cta: string }> = {
  release: {
    title: "Liberar para pago",
    description: "Confirma que habló con el proveedor al número registrado y que la cuenta es legítima.",
    cta: "Liberar",
  },
  reject: {
    title: "Confirmar intento de fraude",
    description: "La factura queda rechazada en el libro y se avisa a Cuentas por pagar y a Compras: no se paga.",
    cta: "Confirmar fraude",
  },
};

export function VerifyActions({ documentId, filingNumber, releaseDepartment }: VerifyActionsProps) {
  const [outcome, setOutcome] = useState<VerificationOutcome | null>(null);
  const [note, setNote] = useState("");
  const [pending, startTransition] = useTransition();

  const submit = () =>
    startTransition(async () => {
      if (!outcome) return;
      const result = await resolveHoldAction(documentId, outcome, note);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success(
        outcome === "release"
          ? `${filingNumber ?? "La factura"} liberada hacia ${departmentLabel[releaseDepartment]}.`
          : `${filingNumber ?? "La factura"} rechazada: se avisó para que no se pague.`,
      );
      setOutcome(null);
      setNote("");
    });

  const copy = outcome ? COPY[outcome] : null;
  return (
    <>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button onClick={() => setOutcome("release")}>
          <ShieldCheck aria-hidden /> Verificada: liberar
        </Button>
        <Button variant="outline" className="text-danger" onClick={() => setOutcome("reject")}>
          <Ban aria-hidden /> Es fraude
        </Button>
      </div>
      <Dialog open={outcome !== null} onOpenChange={(open) => !open && setOutcome(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{copy?.title}</DialogTitle>
            <DialogDescription>{copy?.description}</DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor={`note-${documentId}`} className="flex items-center gap-1.5">
              <PhoneCall aria-hidden className="size-4" /> Nota de la verificación
            </Label>
            <Textarea
              id={`note-${documentId}`}
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Con quién habló, a qué número y qué confirmó"
            />
            <p className="text-caption text-muted-foreground">Queda en el libro y en la auditoría.</p>
          </div>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancelar</Button>
            </DialogClose>
            <Button
              variant={outcome === "reject" ? "destructive" : "default"}
              onClick={submit}
              disabled={pending || note.trim().length < 5}
            >
              {pending ? <Loader2 aria-hidden className="animate-spin" /> : null}
              {copy?.cta}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
