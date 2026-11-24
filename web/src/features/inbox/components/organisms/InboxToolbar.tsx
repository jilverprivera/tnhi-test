"use client";

import { CheckCheck, FolderInput, Loader2, Upload } from "lucide-react";
import { useRef, useState, useTransition } from "react";
import { toast } from "sonner";

import { describeError } from "@/shared/i18n/es";
import { plural } from "@/shared/lib/format";
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

import type { ImportJobResponse } from "@/shared/lib/api-types";

import {
  approveReadyAction,
  enqueueMailboxImportAction,
  enqueueUploadImportAction,
  getImportJobAction,
} from "../../api/inbox-actions";

const POLL_MS = 700;
const MAX_POLLS = 600; // ~7 minutes: month-end batches

/** Follows a queued import until the worker finishes it. */
async function waitForJob(job: ImportJobResponse, onProgress: (job: ImportJobResponse) => void) {
  let current = job;
  for (let i = 0; i < MAX_POLLS && (current.state === "QUEUED" || current.state === "RUNNING"); i++) {
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
    const result = await getImportJobAction(current.id);
    if (!result.ok) return { ok: false as const, code: result.code };
    current = result.data;
    onProgress(current);
  }
  return current.state === "DONE"
    ? { ok: true as const, job: current }
    : { ok: false as const, code: current.error_code ?? "IMPORT_FAILED" };
}

export function InboxToolbar({ readyCount }: { readyCount: number }) {
  const [pending, startTransition] = useTransition();
  const [busy, setBusy] = useState<"mailbox" | "upload" | "approve" | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  function run(kind: typeof busy, task: () => Promise<void>) {
    setBusy(kind);
    startTransition(async () => {
      await task();
      setBusy(null);
    });
  }

  const followJob = async (job: ImportJobResponse) => {
    const toastId = toast.loading("En cola: leyendo correos…");
    const outcome = await waitForJob(job, (j) =>
      toast.loading(j.state === "RUNNING" ? "Procesando correos y preparando propuestas…" : "En cola…", { id: toastId }),
    );
    toast.dismiss(toastId);
    return outcome;
  };

  const importMailbox = () =>
    run("mailbox", async () => {
      const queued = await enqueueMailboxImportAction();
      if (!queued.ok) return void toast.error(describeError(queued.code));
      const result = await followJob(queued.data);
      if (!result.ok) return void toast.error(describeError(result.code));
      const { imported, skipped } = result.job.result ?? { imported: [], skipped: [] };
      toast.success(
        imported.length
          ? `${plural(imported.length, "documento nuevo", "documentos nuevos")} con su propuesta.`
          : "No hay correos nuevos en el buzón.",
        { description: skipped.length ? `${skipped.length} ya estaban en la bandeja.` : undefined },
      );
    });

  const upload = (files: FileList | null) => {
    if (!files?.length) return;
    const form = new FormData();
    Array.from(files).forEach((f) => form.append("files", f));
    run("upload", async () => {
      const queued = await enqueueUploadImportAction(form);
      if (!queued.ok) return void toast.error(describeError(queued.code));
      const result = await followJob(queued.data);
      if (!result.ok) return void toast.error(describeError(result.code));
      const imported = result.job.result?.imported.length ?? 0;
      toast.success(`${plural(imported, "documento importado", "documentos importados")}.`);
      if (fileInput.current) fileInput.current.value = "";
    });
  };

  const approveReady = () =>
    run("approve", async () => {
      const result = await approveReadyAction();
      setConfirmOpen(false);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success(`${plural(result.data.approved, "documento aprobado", "documentos aprobados")}.`, {
        description: `${plural(result.data.filed, "radicado nuevo", "radicados nuevos")} en el libro.`,
      });
    });

  return (
    <>
      <Button variant="outline" onClick={importMailbox} disabled={pending}>
        {busy === "mailbox" ? <Loader2 aria-hidden className="animate-spin" /> : <FolderInput aria-hidden />}
        Leer buzón
      </Button>
      <Button variant="outline" onClick={() => fileInput.current?.click()} disabled={pending}>
        {busy === "upload" ? <Loader2 aria-hidden className="animate-spin" /> : <Upload aria-hidden />}
        Subir .eml
      </Button>
      <input
        ref={fileInput}
        type="file"
        accept=".eml,message/rfc822"
        multiple
        hidden
        aria-label="Subir correos .eml"
        onChange={(e) => upload(e.target.files)}
      />
      <Button onClick={() => setConfirmOpen(true)} disabled={pending || readyCount === 0}>
        <CheckCheck aria-hidden />
        Aprobar listos ({readyCount})
      </Button>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Aprobar {plural(readyCount, "documento listo", "documentos listos")}?</DialogTitle>
            <DialogDescription>
              Se asignan los radicados en orden de llegada, se anotan en el libro y se generan los reenvíos. Lo
              que requiere revisión (incluidas las facturas retenidas) no se toca: eso lo decide usted, uno por uno.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancelar</Button>
            </DialogClose>
            <Button onClick={approveReady} disabled={pending}>
              {busy === "approve" ? <Loader2 aria-hidden className="animate-spin" /> : <CheckCheck aria-hidden />}
              Aprobar y radicar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
