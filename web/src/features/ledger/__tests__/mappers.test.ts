import { parseLedgerQuery, toQueryString } from "../model/mappers";

describe("ledger query", () => {
  it("treats the FilterSelect 'ALL' option as no filter", () => {
    const query = parseLedgerQuery({ q: "FE-1207", department: "ALL", type: "INVOICE" });
    expect(query).toEqual({ q: "FE-1207", department: "", documentType: "INVOICE" });
    expect(toQueryString(query)).toBe("q=FE-1207&document_type=INVOICE");
  });
});

describe("ledger pagination links", () => {
  it("keep the search and move the offset", () => {
    const { ledgerPageHref, parseLedgerOffset } = jest.requireActual("../model/mappers");
    expect(ledgerPageHref({ q: "FE", department: "LEGAL", documentType: "" }, 50)).toBe("/ledger?q=FE&department=LEGAL&offset=50");
    expect(ledgerPageHref({ q: "", department: "", documentType: "" }, 0)).toBe("/ledger");
    expect(parseLedgerOffset({ offset: "-3" })).toBe(0);
  });
});
