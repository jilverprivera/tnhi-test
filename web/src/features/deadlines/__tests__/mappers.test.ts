import { daysLeftLabel, toWeeklyReportView } from "../model/mappers";

describe("deadline mappers", () => {
  it("labels business days left in Spanish", () => {
    expect(daysLeftLabel(-2)).toBe("Vencido hace 2 días hábiles");
    expect(daysLeftLabel(0)).toBe("Vence hoy");
    expect(daysLeftLabel(1)).toBe("1 día hábil");
  });

  it("marks documents not filed yet", () => {
    const view = toWeeklyReportView({
      today: "2026-11-18",
      week_start: "2026-11-16",
      week_end: "2026-11-22",
      overdue: [],
      this_week: [],
      next_week: [
        {
          filing_number: null,
          document_id: "11.eml__0",
          document_type: "OVERSIGHT_NOTICE",
          department: "LEGAL",
          sender: "Ventanilla Contraloría",
          subject: "Notificación oficio CD-2026-3345",
          received_date: "2026-11-13",
          due_date: "2026-11-23",
          urgent: true,
          state: "DUE_NEXT_WEEK",
          business_days_left: 3,
        },
      ],
      not_filed_yet: 1,
    });
    expect(view.nextWeek[0].isFiled).toBe(false);
    expect(view.nextWeek[0].key).toBe("11.eml__0");
  });
});

describe("dateParts", () => {
  it("splits a date for calendar tiles", () => {
    const { dateParts } = jest.requireActual("@/shared/lib/format");
    expect(dateParts("2026-11-23")).toEqual({ day: "23", month: "nov" });
  });
});

describe("formatDateNumeric", () => {
  it("formats dates compactly for tables", () => {
    const { formatDateNumeric } = jest.requireActual("@/shared/lib/format");
    expect(formatDateNumeric("2026-11-09")).toBe("09/11/2026");
    expect(formatDateNumeric(null)).toBe("—");
  });
});
