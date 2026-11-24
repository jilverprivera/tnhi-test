"use client";

import { Loader2, Trash2 } from "lucide-react";
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
import { Input } from "@/shared/ui/primitives/input";
import { Label } from "@/shared/ui/primitives/label";

import { disposeRecordAction } from "../../api/compliance-actions";

export function DisposeButton({ filingNumber }: { filingNumber: string }) {
  const [reference, setReference] = useState("");
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const dispose = () =>
    startTransition(async () => {
      const result = await disposeRecordAction(filingNumber, reference);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success(`${filingNumber}: contenido eliminado; el índice queda en el libro.`);
      setOpen(false);
    });
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="text-danger">
          <Trash2 aria-hidden /> Eliminar
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Eliminar {filingNumber}</DialogTitle>
          <DialogDescription>
            Se borran el archivo original y el texto con datos personales. La fila del libro se conserva como índice, con la
            fecha y el acta.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5">
          <Label htmlFor={`acta-${filingNumber}`}>Acta de eliminación del comité de archivo</Label>
          <Input id={`acta-${filingNumber}`} value={reference} onChange={(e) => setReference(e.target.value)} placeholder="Ej.: Acta 03 de 2037" />
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancelar</Button>
          </DialogClose>
          <Button variant="destructive" onClick={dispose} disabled={pending || reference.trim().length < 3}>
            {pending ? <Loader2 aria-hidden className="animate-spin" /> : null}
            Eliminar contenido
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
