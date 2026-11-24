import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DatePicker } from "@/shared/ui/molecules/DatePicker";

describe("DatePicker", () => {
  it("shows the date in Spanish on a design-system button, not a native date input", () => {
    const { container } = render(
      <form>
        <DatePicker id="d" name="on" defaultValue="2026-11-23" />
      </form>,
    );
    expect(container.querySelector('input[type="date"]')).toBeNull();
    expect(screen.getByRole("button")).toHaveTextContent("23 de nov de 2026");
    expect(container.querySelector('input[name="on"]')).toHaveValue("2026-11-23");
  });

  it("opens its own calendar in Spanish and clears the value", async () => {
    const user = userEvent.setup();
    const changes: string[] = [];
    render(<DatePicker id="d" defaultValue="2026-11-23" today="2026-11-18" onChange={(v) => changes.push(v)} />);
    await user.click(screen.getByRole("button"));
    expect(await screen.findByRole("grid")).toBeInTheDocument();
    expect(screen.getAllByText(/noviembre|nov/i).length).toBeGreaterThan(0);
    await user.click(screen.getByRole("button", { name: /Borrar/ }));
    expect(changes).toEqual([""]);
  });
});
