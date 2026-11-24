import { render, screen } from "@testing-library/react";

import { FilterSelect } from "@/shared/ui/molecules/FilterSelect";

describe("FilterSelect", () => {
  it("renders a design-system trigger (combobox) with the current label, not a native select", () => {
    render(
      <form>
        <FilterSelect
          id="dep"
          name="department"
          label="Dependencia"
          allLabel="Todas las dependencias"
          options={[{ value: "LEGAL", label: "Jurídica" }]}
          defaultValue="LEGAL"
        />
      </form>,
    );
    const trigger = screen.getByRole("combobox", { name: "Dependencia" });
    expect(trigger.tagName).toBe("BUTTON");
    expect(trigger).toHaveTextContent("Jurídica");
  });
});
