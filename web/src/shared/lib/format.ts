/** Colombian formats: dates as "17 nov 2026", money as "$ 7.497.000". */

const BOGOTA = "America/Bogota";

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = iso.length === 10 ? new Date(`${iso}T12:00:00-05:00`) : new Date(iso);
  return new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short", year: "numeric", timeZone: BOGOTA })
    .format(date)
    .replace(".", "");
}

/** "09/11/2026": compact, for dense tables (tabular figures align it). */
export function formatDateNumeric(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = iso.length === 10 ? new Date(`${iso}T12:00:00-05:00`) : new Date(iso);
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: BOGOTA }).format(date);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: BOGOTA,
  })
    .format(new Date(iso))
    .replace(".", "");
}

/** {day: "23", month: "nov"} for compact calendar tiles. */
export function dateParts(iso: string): { day: string; month: string } {
  const date = new Date(`${iso}T12:00:00-05:00`);
  const fmt = (o: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("es-CO", { ...o, timeZone: BOGOTA }).format(date);
  return { day: fmt({ day: "numeric" }), month: fmt({ month: "short" }).replace(".", "") };
}

export function formatMoney(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);
}

export function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}
