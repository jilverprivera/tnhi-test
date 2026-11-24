import { inboxItem } from "@/features/inbox/__tests__/mappers.test";
import type { HeldInvoiceResponse } from "@/shared/lib/api-types";

import { splitByState, toHeldInvoiceView } from "../model/mappers";

function held(overrides: Partial<HeldInvoiceResponse> = {}): HeldInvoiceResponse {
  return {
    ...inboxItem({ status: "APPROVED", filing_number: "TAC-2026-ER-04826" }),
    verification_state: "AWAITING_VERIFICATION",
    release_department: "ACCOUNTS_PAYABLE",
    hold_resolution: null,
    master_supplier: {
      nit: "901.112.233-4",
      name: "Aseo Integral Bogotá S.A.S.",
      billing_email: "facturacion@aseointegralbogota.example",
      bank: "BBVA",
      account_type: "Corriente",
      account_number: "0013-0456-78-0100012345",
      status: "ACTIVO",
      category: "Aseo y cafetería",
      is_active: true,
    },
    ...overrides,
  };
}

describe("held invoice mapper", () => {
  it("puts what arrived next to what the master says and flags both mismatches", () => {
    const view = toHeldInvoiceView(held());
    const [account, email] = view.comparisons;
    expect(account.isMismatch).toBe(true);
    expect(account.master).toContain("0013-0456-78-0100012345");
    expect(email.isMismatch).toBe(true);
    expect(view.masterContact).toContain("facturacion@aseointegralbogota.example");
    expect(view.reasons.length).toBeGreaterThan(0);
  });

  it("tells unregistered suppliers apart", () => {
    expect(toHeldInvoiceView(held({ master_supplier: null })).masterContact).toMatch(/no registrado/);
  });

  it("splits by who has to act", () => {
    const items = [
      toHeldInvoiceView(held()),
      toHeldInvoiceView(held({ id: "x", verification_state: "PENDING_CLERK_APPROVAL" })),
      toHeldInvoiceView(held({ id: "y", verification_state: "RELEASED" })),
    ];
    const groups = splitByState(items);
    expect([groups.awaiting.length, groups.withClerk.length, groups.resolved.length]).toEqual([1, 1, 1]);
  });
});
