"use client";

import { Loader2, ShieldAlert } from "lucide-react";
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

import { escalateHoldAction } from "../../api/document-actions";

/** A suspected fraud is never approved: the clerk hands it to Dra. Herrera, who calls the supplier. */
export function EscalateHoldButton({ documentId, onDone }: { documentId: string; onDone: () => void }) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const escalate = () =>
    startTransition(async () => {
      const result = await escalateHoldAction(documentId);
      if (!result.ok) return void toast.error(describeError(result.code));
      setOpen(false);
      toast.success("Alerta enviada a la Dra. Herrera", {
        description: `Quedó radicada como retenida${result.data.filingNumber ? ` (${result.data.filingNumber})` : ""}; no se envía a pago.`,
      });
      onDone();
    });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="destructive" className="h-11">
          <ShieldAlert aria-hidden /> Alertar a la Dra. Herrera
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>¿Alertar posible fraude?</DialogTitle>
          <DialogDescription>
            La factura no se aprueba ni se envía a pago. Queda radicada como <b>retenida</b> para que haya constancia del intento,
            y la Dra. Herrera la verifica llamando al proveedor al número del maestro (nunca al del correo). Ella decide si se libera
            o si es fraude.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancelar</Button>
          </DialogClose>
          <Button variant="destructive" onClick={escalate} disabled={pending}>
            {pending ? <Loader2 aria-hidden className="animate-spin" /> : <ShieldAlert aria-hidden />}
            Enviar alerta
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
