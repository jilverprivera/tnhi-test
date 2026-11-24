import { inboxItem } from "@/features/inbox/__tests__/mappers.test";

import { toDocumentDetailView } from "../model/mappers";
import { documentCorrectionSchema } from "../model/schemas";

describe("document review mappers", () => {
  it("puts blocking reasons first and flags the account mismatch field", () => {
    const view = toDocumentDetailView(inboxItem());
    expect(view.reasons.every((r, i, all) => i === 0 || !r.isBlocking || all[i - 1].isBlocking)).toBe(true);
    const account = view.fields.find((f) => f.label === "Cuenta en la factura");
    expect(account?.emphasis).toBe("danger");
    expect(view.fields.find((f) => f.label === "Total")?.value).toMatch(/7\.497\.000/);
  });

  it("travel requests show approval and departure", () => {
    const item = inboxItem();
    item.decision = { ...item.decision, document_type: "TRAVEL_EXPENSE_REQUEST", late: true, reasons: [] };
    item.data = { ...item.data, approver: "", approver_signed: false, departure_date: "2026-11-19" };
    const labels = Object.fromEntries(toDocumentDetailView(item).fields.map((f) => [f.label, f]));
    expect(labels["Aprobado por"].emphasis).toBe("danger");
    expect(labels["Fecha de salida"].emphasis).toBe("warning");
  });
});

describe("correction schema", () => {
  const base = { documentType: "INVOICE", department: "ACCOUNTS_PAYABLE", action: "FILE", dueDate: "", isUrgent: false, notes: "" } as const;

  it("accepts a complete correction", () => {
    expect(documentCorrectionSchema.safeParse(base).success).toBe(true);
  });

  it("rejects filing without a department", () => {
    const result = documentCorrectionSchema.safeParse({ ...base, department: "NONE" });
    expect(result.success).toBe(false);
  });

  it("rejects malformed dates", () => {
    expect(documentCorrectionSchema.safeParse({ ...base, dueDate: "18/11/2026" }).success).toBe(false);
  });
});

describe("correction schema for held invoices", () => {
  it("rejects holding without a department", () => {
    const result = documentCorrectionSchema.safeParse({
      documentType: "INVOICE",
      department: "NONE",
      action: "HOLD_FOR_VERIFICATION",
      dueDate: "",
      isUrgent: false,
      notes: "",
    });
    expect(result.success).toBe(false);
  });
});
