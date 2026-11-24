import type { DeadlineResponse, WeeklyReportResponse } from "@/shared/lib/api-types";

import type { DeadlineView, WeeklyReportView } from "./types";

export function toDeadlineView(d: DeadlineResponse): DeadlineView {
  return {
    key: d.filing_number ?? d.document_id ?? `${d.subject}-${d.due_date}`,
    filingNumber: d.filing_number,
    documentId: d.document_id,
    documentType: d.document_type,
    department: d.department,
    sender: d.sender,
    subject: d.subject,
    receivedDate: d.received_date,
    dueDate: d.due_date,
    isUrgent: d.urgent,
    state: d.state,
    businessDaysLeft: d.business_days_left,
    isFiled: d.filing_number !== null,
  };
}

export function toWeeklyReportView(r: WeeklyReportResponse): WeeklyReportView {
  return {
    today: r.today,
    weekStart: r.week_start,
    weekEnd: r.week_end,
    overdue: r.overdue.map(toDeadlineView),
    thisWeek: r.this_week.map(toDeadlineView),
    nextWeek: r.next_week.map(toDeadlineView),
    notFiledYet: r.not_filed_yet,
  };
}

export function daysLeftLabel(days: number): string {
  if (days < 0) return `Vencido hace ${Math.abs(days)} ${Math.abs(days) === 1 ? "día hábil" : "días hábiles"}`;
  if (days === 0) return "Vence hoy";
  return `${days} ${days === 1 ? "día hábil" : "días hábiles"}`;
}
