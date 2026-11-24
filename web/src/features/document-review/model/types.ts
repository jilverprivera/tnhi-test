import type { Action, Department, DocumentStatus, DocumentType } from "@/shared/lib/api-types";

export interface ReasonView {
  code: string;
  text: string;
  isBlocking: boolean;
}

export interface FieldView {
  label: string;
  value: string;
  emphasis?: "danger" | "warning";
  isMono?: boolean;
}

export interface DecisionView {
  documentType: DocumentType;
  department: Department;
  action: Action;
  dueDate: string | null;
  isUrgent: boolean;
  isLate: boolean;
  existingFilingNumber: string | null;
}

export interface AuditView {
  at: string;
  actor: string;
  event: string;
}

export interface DocumentDetailView {
  id: string;
  status: DocumentStatus;
  decision: DecisionView;
  proposal: DecisionView;
  wasCorrected: boolean;
  needsReview: boolean;
  confidence: number;
  filingNumber: string | null;
  notes: string;
  receivedAt: string;
  sender: string;
  senderName: string;
  subject: string;
  documentName: string;
  isEmailBody: boolean;
  extractionMethod: string;
  ocrConfidence: number | null;
  text: string;
  emailBody: string;
  reasons: ReasonView[];
  fields: FieldView[];
  audit: AuditView[];
}
