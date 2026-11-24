import type { Disposition, RetentionStatus } from "@/shared/lib/api-types";

export const dispositionLabel: Record<Disposition, string> = {
  CONSERVE: "Conservación total",
  DESTROY: "Eliminación",
  SELECT: "Selección (comité)",
};

export const retentionStatusLabel: Record<RetentionStatus, string> = {
  ACTIVE: "Vigente",
  DUE_FOR_DISPOSITION: "Cumplió retención",
  DISPOSED: "Eliminado",
};

export const matchFieldLabel: Record<string, string> = {
  identification: "Identificación",
  sender: "Remitente",
  document_text: "Texto del documento",
  email_body: "Cuerpo del correo",
};

/** "on" lets the coordinator preview what will be due at a future date (YYYY-MM-DD). */
export function parsePreviewDate(value: string | string[] | undefined): string | null {
  const v = Array.isArray(value) ? value[0] : value;
  return v && /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : null;
}
