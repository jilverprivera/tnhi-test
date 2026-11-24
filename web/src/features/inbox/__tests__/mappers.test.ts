import type { InboxItemResponse } from "@/shared/lib/api-types";

import { applyFilter, parseFilter, sortForWork, toInboxItemView } from "../model/mappers";

export function inboxItem(overrides: Partial<InboxItemResponse> = {}): InboxItemResponse {
  return {
    id: "05.eml__0",
    status: "NEEDS_REVIEW",
    filing_number: null,
    received_at: "2026-11-17T07:48:00-05:00",
    needs_review: true,
    was_corrected: false,
    notes: "",
    document: {
      email_file: "05.eml",
      position: 0,
      name: "AIB-2026-1189.pdf",
      sender: "facturacion@aseointegral-bogota.example",
      sender_name: "Facturación Aseo Integral",
      email_subject: "Factura noviembre + IMPORTANTE cambio de cuenta",
      extraction_method: "PDF_TEXT",
      ocr_confidence: null,
    },
    data: {
      sender_name: "Aseo Integral Bogotá S.A.S.",
      identification: "901.112.233-4",
      document_number: "AIB-2026-1189",
      total_amount: 7497000,
      subtotal: 6300000,
      tax: 1197000,
      purchase_order: "OC-2026-0377",
      bank_account: "912-345678-90",
      bank: "Bancolombia",
      issue_date: "2026-11-14",
      departure_date: null,
      approver: "",
      approver_signed: false,
      has_official_form: false,
      term_days: null,
      term_kind: "",
      mentions_tutela: false,
    },
    decision: {
      document_type: "INVOICE",
      department: "ADMIN_COORDINATION",
      action: "HOLD_FOR_VERIFICATION",
      due_date: null,
      urgent: false,
      late: false,
      reasons: [
        { code: "INVOICE_ACCOUNT_MISMATCH", params: { invoice: "912-345678-90", master: "0013-0456-78-0100012345" }, blocking: true },
        { code: "SENDER_DOMAIN_MISMATCH", params: { sender: "aseointegral-bogota.example", master: "aseointegralbogota.example" }, blocking: true },
      ],
      evidence: [],
      confidence: 0.5,
      existing_filing_number: null,
    },
    ...overrides,
  };
}

describe("inbox mappers", () => {
  it("maps the API item to a view with the blocking reasons in Spanish", () => {
    const view = toInboxItemView(inboxItem());
    expect(view.senderName).toBe("Aseo Integral Bogotá S.A.S.");
    expect(view.action).toBe("HOLD_FOR_VERIFICATION");
    expect(view.blockingReasons[0]).toContain("no es la del maestro");
  });

  it("uses the e-mail body label for body documents", () => {
    const item = inboxItem();
    item.document.name = "EMAIL_BODY";
    expect(toInboxItemView(item).documentName).toBe("Cuerpo del correo");
  });

  it("filters and puts what needs review first", () => {
    const review = toInboxItemView(inboxItem({ id: "b", received_at: "2026-11-17T10:00:00-05:00" }));
    const ready = toInboxItemView(inboxItem({ id: "a", status: "READY", needs_review: false, received_at: "2026-11-10T08:00:00-05:00" }));
    const approved = toInboxItemView(inboxItem({ id: "c", status: "APPROVED", needs_review: false }));
    const all = [ready, review, approved];
    expect(applyFilter(all, "pending").map((i) => i.id)).toEqual(["a", "b"]);
    expect(applyFilter(all, "approved").map((i) => i.id)).toEqual(["c"]);
    expect(sortForWork(applyFilter(all, "pending")).map((i) => i.id)).toEqual(["b", "a"]);
  });

  it("parses unknown filters as pending", () => {
    expect(parseFilter("nonsense")).toBe("pending");
    expect(parseFilter(["review"])).toBe("review");
  });
});
