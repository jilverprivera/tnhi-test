"use client";

import { Printer } from "lucide-react";

import { Button } from "@/shared/ui/primitives/button";

export function PrintButton() {
  return (
    <Button variant="outline" className="h-11 print:hidden" onClick={() => window.print()}>
      <Printer aria-hidden /> Imprimir reporte
    </Button>
  );
}
