import type { Department, VerificationState } from "@/shared/lib/api-types";

export interface ComparisonView {
  label: string;
  received: string;
  master: string;
  isMismatch: boolean;
}

export interface HeldInvoiceView {
  id: string;
  state: VerificationState;
  filingNumber: string | null;
  receivedAt: string;
  supplierName: string;
  invoiceNumber: string;
  totalAmount: number | null;
  purchaseOrder: string;
  sender: string;
  subject: string;
  reasons: string[];
  comparisons: ComparisonView[];
  masterContact: string;
  releaseDepartment: Department;
  resolution: { outcome: "RELEASED" | "REJECTED"; note: string; at: string } | null;
}
