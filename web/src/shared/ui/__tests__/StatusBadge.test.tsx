import { render, screen } from "@testing-library/react";

import { describeReason } from "@/shared/i18n/es";
import { documentPresentation, DocumentStatusBadge } from "@/shared/ui/molecules/DocumentStatusBadge";

describe("DocumentStatusBadge", () => {
  it("shows a held invoice as possible fraud, not just 'needs review'", () => {
    render(<DocumentStatusBadge status="NEEDS_REVIEW" action="HOLD_FOR_VERIFICATION" />);
    expect(screen.getByText("Retenida: posible fraude")).toBeInTheDocument();
  });

  it.each([
    ["READY", "FILE", "success"],
    ["NEEDS_REVIEW", "FILE", "warning"],
    ["READY", "REPLY_WITH_EXISTING_NUMBER", "duplicate"],
    ["READY", "RETURN_TO_SENDER", "info"],
    ["APPROVED", "FILE", "primary"],
  ] as const)("%s + %s -> %s tone", (status, action, tone) => {
    expect(documentPresentation(status, action).tone).toBe(tone);
  });
});

describe("reason labels", () => {
  it("interpolates params and never shows a raw code to the user", () => {
    expect(describeReason("INVOICE_DUPLICATE", { filing_number: "TAC-2026-ER-04790" })).toContain("TAC-2026-ER-04790");
    expect(describeReason("UNKNOWN_CODE")).toBe("Hay un motivo para revisar este documento.");
  });
});
