import { render, screen } from "@testing-library/react";

import { ReasonList } from "../components/molecules/ReasonList";

describe("ReasonList", () => {
  it("shows the explanation without the internal code", () => {
    render(<ReasonList reasons={[{ code: "DOCUMENT_UNREADABLE", text: "No se pudo leer el documento: revíselo a mano.", isBlocking: true }]} />);
    expect(screen.getByText(/No se pudo leer el documento/)).toBeInTheDocument();
    expect(screen.queryByText(/DOCUMENT_UNREADABLE/)).not.toBeInTheDocument();
  });
});
