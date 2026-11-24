import type { Department, DocumentType, LedgerStatus } from "@/shared/lib/api-types";

export interface LedgerEntryView {
  filingNumber: string;
  receivedDate: string;
  sender: string;
  identification: string;
  documentType: DocumentType;
  subject: string;
  documentNumber: string;
  totalAmount: number | null;
  department: Department;
  dueDate: string | null;
  status: LedgerStatus;
  notes: string;
  isUrgent: boolean;
  isNew: boolean; // filed by Docket (not imported from the historical Excel)
}

export interface LedgerQueryView {
  q: string;
  department: string;
  documentType: string;
}
