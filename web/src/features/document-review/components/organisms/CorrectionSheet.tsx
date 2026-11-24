"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, PencilLine } from "lucide-react";
import { useState, useTransition } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { actionLabel, departmentLabel, describeError, documentTypeLabel } from "@/shared/i18n/es";
import { ACTIONS, DEPARTMENTS, DOCUMENT_TYPES } from "@/shared/lib/api-types";
import { Button } from "@/shared/ui/primitives/button";
import { DatePicker } from "@/shared/ui/molecules/DatePicker";
import { Checkbox } from "@/shared/ui/primitives/checkbox";
import { Label } from "@/shared/ui/primitives/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/primitives/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/shared/ui/primitives/sheet";
import { Textarea } from "@/shared/ui/primitives/textarea";

import { correctDocumentAction } from "../../api/document-actions";
import { documentCorrectionSchema, type DocumentCorrectionValues } from "../../model/schemas";
import type { DecisionView } from "../../model/types";


interface CorrectionSheetProps {
  documentId: string;
  decision: DecisionView;
  notes: string;
  today: string;
}

function SelectField<T extends string>({
  id,
  label,
  value,
  onChange,
  options,
  labels,
  error,
}: {
  id: string;
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: readonly T[];
  labels: Record<T, string>;
  error?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Select value={value} onValueChange={(v) => onChange(v as T)}>
        <SelectTrigger id={id} className="h-11 w-full" aria-invalid={error ? true : undefined}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o} value={o}>
              {labels[o]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error ? <p className="text-caption text-danger" role="alert">{error}</p> : null}
    </div>
  );
}

export function CorrectionSheet({ documentId, decision, notes, today }: CorrectionSheetProps) {
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const form = useForm<DocumentCorrectionValues>({
    resolver: zodResolver(documentCorrectionSchema),
    defaultValues: {
      documentType: decision.documentType,
      department: decision.department,
      action: decision.action,
      dueDate: decision.dueDate ?? "",
      isUrgent: decision.isUrgent,
      notes,
    },
  });
  const { errors } = form.formState;

  const submit = form.handleSubmit((values) =>
    startTransition(async () => {
      const result = await correctDocumentAction(documentId, values);
      if (!result.ok) return void toast.error(describeError(result.code));
      toast.success("Corrección guardada. Revise y apruebe cuando esté conforme.");
      setOpen(false);
    }),
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" className="h-11">
          <PencilLine aria-hidden /> Corregir
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Corregir la propuesta</SheetTitle>
          <SheetDescription>La propuesta original del sistema se conserva para la auditoría.</SheetDescription>
        </SheetHeader>
        <form id="correction-form" onSubmit={submit} className="space-y-4 px-4">
          <Controller
            control={form.control}
            name="documentType"
            render={({ field }) => (
              <SelectField id="documentType" label="Qué es" value={field.value} onChange={field.onChange} options={DOCUMENT_TYPES} labels={documentTypeLabel} />
            )}
          />
          <Controller
            control={form.control}
            name="department"
            render={({ field }) => (
              <SelectField
                id="department"
                label="Va para"
                value={field.value}
                onChange={field.onChange}
                options={DEPARTMENTS}
                labels={departmentLabel}
                error={errors.department?.message}
              />
            )}
          />
          <Controller
            control={form.control}
            name="action"
            render={({ field }) => (
              <SelectField id="action" label="Acción" value={field.value} onChange={field.onChange} options={ACTIONS} labels={actionLabel} />
            )}
          />
          <div className="space-y-1.5">
            <Label htmlFor="dueDate">Fecha de vencimiento</Label>
            <Controller
              control={form.control}
              name="dueDate"
              render={({ field }) => (
                <DatePicker
                  id="dueDate"
                  value={field.value}
                  onChange={field.onChange}
                  today={today}
                  aria-invalid={errors.dueDate ? true : undefined}
                />
              )}
            />
            <p className="text-caption text-muted-foreground">Déjela vacía si no aplica.</p>
          </div>
          <Controller
            control={form.control}
            name="isUrgent"
            render={({ field }) => (
              <label className="flex min-h-11 items-center gap-3 text-body-sm">
                <Checkbox checked={field.value} onCheckedChange={(v) => field.onChange(v === true)} />
                Marcar como urgente
              </label>
            )}
          />
          <div className="space-y-1.5">
            <Label htmlFor="notes">Observaciones para el libro</Label>
            <Textarea id="notes" rows={3} {...form.register("notes")} />
            {errors.notes ? <p className="text-caption text-danger">{errors.notes.message}</p> : null}
          </div>
        </form>
        <SheetFooter>
          <Button type="submit" form="correction-form" className="h-11" disabled={pending}>
            {pending ? <Loader2 aria-hidden className="animate-spin" /> : null}
            Guardar corrección
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
