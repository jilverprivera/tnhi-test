/**
 * Shapes and code unions of the Docket API (mirror of api/app/shared/domain/models.py).
 * Keys are snake_case as sent by the API; features map them to camelCase view models.
 */

export const DOCUMENT_TYPES = [
  "INVOICE",
  "TRAVEL_EXPENSE_REQUEST",
  "PETITION",
  "OVERSIGHT_NOTICE",
  "COMPLAINT",
  "QUOTATION",
  "ADVERTISING",
  "OTHER",
] as const;
export type DocumentType = (typeof DOCUMENT_TYPES)[number];

export const DEPARTMENTS = [
  "ACCOUNTS_PAYABLE",
  "PROCUREMENT",
  "HUMAN_RESOURCES",
  "LEGAL",
  "CUSTOMER_SERVICE",
  "ADMIN_COORDINATION",
  "SENDER",
  "NONE",
] as const;
export type Department = (typeof DEPARTMENTS)[number];

export const ACTIONS = [
  "FILE",
  "RETURN_TO_SENDER",
  "DO_NOT_FILE",
  "REPLY_WITH_EXISTING_NUMBER",
  "HOLD_FOR_VERIFICATION",
] as const;
export type Action = (typeof ACTIONS)[number];

export const DOCUMENT_STATUSES = ["READY", "NEEDS_REVIEW", "APPROVED", "DISCARDED"] as const;
export type DocumentStatus = (typeof DOCUMENT_STATUSES)[number];

export type LedgerStatus = "DELIVERED" | "IN_PROGRESS" | "ON_HOLD" | "REJECTED" | "CLOSED";
export type DeadlineState = "OVERDUE" | "DUE_TODAY" | "DUE_THIS_WEEK" | "DUE_NEXT_WEEK" | "LATER";
export type OutboxKind =
  | "FORWARD_TO_DEPARTMENT"
  | "RETURN_TO_SENDER"
  | "REPLY_EXISTING_NUMBER"
  | "FRAUD_ALERT"
  | "FRAUD_CONFIRMED";
export type Role = "CLERK" | "COORDINATOR";

export interface Envelope<T> {
  code: string;
  data: T;
}

export interface ErrorResponse {
  code: string;
  detail?: Record<string, unknown>;
}

export interface ReasonResponse {
  code: string;
  params: Record<string, string>;
  blocking: boolean;
}

export interface EvidenceResponse {
  field: string;
  value: string;
  source: string;
}

export interface DecisionResponse {
  document_type: DocumentType;
  department: Department;
  action: Action;
  due_date: string | null;
  urgent: boolean;
  late: boolean;
  reasons: ReasonResponse[];
  evidence: EvidenceResponse[];
  confidence: number;
  existing_filing_number: string | null;
}

export interface ExtractedDataResponse {
  sender_name: string;
  identification: string;
  document_number: string;
  total_amount: number | null;
  subtotal: number | null;
  tax: number | null;
  purchase_order: string;
  bank_account: string;
  bank: string;
  issue_date: string | null;
  departure_date: string | null;
  approver: string;
  approver_signed: boolean;
  has_official_form: boolean;
  term_days: number | null;
  term_kind: string;
  mentions_tutela: boolean;
}

export interface DocumentInfoResponse {
  email_file: string;
  position: number;
  name: string;
  sender: string;
  sender_name: string;
  email_subject: string;
  extraction_method: string;
  ocr_confidence: number | null;
  text?: string;
  email_body?: string;
}

export interface AuditEventResponse {
  at: string;
  actor: string;
  event: string;
  document_id: string | null;
  details: Record<string, unknown>;
}

export interface InboxItemResponse {
  id: string;
  status: DocumentStatus;
  filing_number: string | null;
  received_at: string;
  needs_review: boolean;
  was_corrected: boolean;
  notes: string;
  document: DocumentInfoResponse;
  data: ExtractedDataResponse;
  decision: DecisionResponse;
  proposal_decision?: DecisionResponse;
  audit?: AuditEventResponse[];
}

export type InboxSummaryResponse = Record<DocumentStatus, number>;

export interface LedgerEntryResponse {
  filing_number: string;
  received_date: string;
  sender: string;
  identification: string;
  document_type: DocumentType;
  subject: string;
  document_number: string;
  total_amount: number | null;
  department: Department;
  due_date: string | null;
  status: LedgerStatus;
  notes: string;
  flags: string[];
  urgent: boolean;
  source_document_id: string | null;
}

export interface DeadlineResponse {
  filing_number: string | null;
  document_id: string | null;
  document_type: DocumentType;
  department: Department;
  sender: string;
  subject: string;
  received_date: string;
  due_date: string;
  urgent: boolean;
  state: DeadlineState;
  business_days_left: number;
}

export interface WeeklyReportResponse {
  today: string;
  week_start: string;
  week_end: string;
  overdue: DeadlineResponse[];
  this_week: DeadlineResponse[];
  next_week: DeadlineResponse[];
  not_filed_yet: number;
}

export interface OutboxMessageResponse {
  kind: OutboxKind;
  document_id: string;
  to_address: string;
  subject: string;
  body: string;
}

export interface SupplierResponse {
  nit: string;
  name: string;
  billing_email: string;
  bank: string;
  account_type: string;
  account_number: string;
  status: string;
  category: string;
  is_active: boolean;
}

export interface DepartmentResponse {
  code: Department;
  client_code: string;
  name: string;
  email: string;
  receives: string;
}

export interface ImportResultResponse {
  imported: string[];
  skipped: string[];
  failed: Record<string, string>;
}

export interface SessionResponse {
  role: Role;
  today: string;
}

export type VerificationState = "PENDING_CLERK_APPROVAL" | "AWAITING_VERIFICATION" | "RELEASED" | "REJECTED";

export interface HoldResolutionResponse {
  outcome: "RELEASED" | "REJECTED";
  note: string;
  actor: string;
  at: string;
}

export interface HeldInvoiceResponse extends InboxItemResponse {
  verification_state: VerificationState;
  release_department: Department;
  hold_resolution: HoldResolutionResponse | null;
  master_supplier: SupplierResponse | null;
}

export interface PageResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type ImportJobState = "QUEUED" | "RUNNING" | "DONE" | "FAILED";

export interface ImportJobResponse {
  id: string;
  state: ImportJobState;
  source: "MAILBOX" | "UPLOAD";
  actor: string;
  file_count: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result: ImportResultResponse | null;
  error_code: string | null;
}

export type RetentionStatus = "ACTIVE" | "DUE_FOR_DISPOSITION" | "DISPOSED";
export type Disposition = "CONSERVE" | "DESTROY" | "SELECT";

export interface RetentionRuleResponse {
  document_type: DocumentType;
  office_years: number;
  central_years: number;
  total_years: number;
  disposition: Disposition;
  basis: string;
}

export interface RetentionViewResponse {
  filing_number: string;
  document_type: DocumentType;
  received_date: string;
  retention_ends: string;
  disposition: Disposition;
  status: RetentionStatus;
}

export interface PersonalDataItemResponse {
  data: string;
  subjects: string;
  stored_in: string;
  purpose: string;
  legal_basis: string;
  access: string;
  retention: string;
}

export interface SubjectReportResponse {
  kind: "INQUIRY" | "CLAIM";
  identifier_masked: string;
  response_due: string;
  matches: { where: "LEDGER" | "INBOX"; reference: string; fields: string[]; received_date: string; content_available: boolean }[];
}

export interface ReadinessResponse {
  checks: Record<string, "OK" | "DEGRADED" | "DOWN" | "MISSING">;
}

export interface LedgerSyncStateResponse {
  outcome: "SYNCED" | "SYNCED_WITH_CONFLICTS" | "LOCKED" | "CHANGED_TOO_OFTEN";
  at: string;
  imported_rows: number;
  restored_rows: number;
  merged_from_excel: number;
  written_to_excel: number;
  conflicts: { filing_number: string; column: string }[];
}
