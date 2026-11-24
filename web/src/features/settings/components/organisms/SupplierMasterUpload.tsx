"use client";

import { FileUp, Loader2 } from "lucide-react";
import { useRef, useTransition } from "react";
import { toast } from "sonner";

import { describeError } from "@/shared/i18n/es";
import { Button } from "@/shared/ui/primitives/button";

import { replaceSupplierMasterAction } from "../../api/settings-actions";

export function SupplierMasterUpload() {
  const input = useRef<HTMLInputElement>(null);
  const [pending, startTransition] = useTransition();
  const upload = (file: File | undefined) => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    startTransition(async () => {
      const result = await replaceSupplierMasterAction(form);
      if (!result.ok) toast.error(describeError(result.code));
      else toast.success(`Maestro actualizado: ${result.data.suppliers} proveedores.`);
      if (input.current) input.current.value = "";
    });
  };
  return (
    <>
      <Button variant="outline" className="h-11" onClick={() => input.current?.click()} disabled={pending}>
        {pending ? <Loader2 aria-hidden className="animate-spin" /> : <FileUp aria-hidden />}
        Cargar maestro del ERP (.csv)
      </Button>
      <input ref={input} type="file" accept=".csv,text/csv" hidden aria-label="Maestro de proveedores CSV" onChange={(e) => upload(e.target.files?.[0])} />
    </>
  );
}
