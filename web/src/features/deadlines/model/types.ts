import type { DeadlineState, Department, DocumentType } from "@/shared/lib/api-types";

export interface DeadlineView {
  key: string;
  filingNumber: string | null;
  documentId: string | null;
  documentType: DocumentType;
  department: Department;
  sender: string;
  subject: string;
  receivedDate: string;
  dueDate: string;
  isUrgent: boolean;
  state: DeadlineState;
  businessDaysLeft: number;
  isFiled: boolean;
}

export interface WeeklyReportView {
  today: string;
  weekStart: string;
  weekEnd: string;
  overdue: DeadlineView[];
  thisWeek: DeadlineView[];
  nextWeek: DeadlineView[];
  notFiledYet: number;
}
