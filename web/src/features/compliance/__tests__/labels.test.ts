import { dispositionLabel, parsePreviewDate } from "../model/labels";

describe("compliance labels", () => {
  it("accepts only ISO dates for the preview", () => {
    expect(parsePreviewDate("2037-01-02")).toBe("2037-01-02");
    expect(parsePreviewDate("02/01/2037")).toBeNull();
    expect(parsePreviewDate(undefined)).toBeNull();
  });

  it("names every disposition", () => {
    expect(dispositionLabel.DESTROY).toBe("Eliminación");
  });
});
