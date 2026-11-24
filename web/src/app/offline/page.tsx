import type { Metadata } from "next";
import { WifiOff } from "lucide-react";

export const metadata: Metadata = { title: "Sin conexión" };

export default function OfflinePage() {
  return (
    <main className="grid min-h-dvh place-items-center px-6 text-center">
      <div className="max-w-sm space-y-3">
        <WifiOff aria-hidden className="mx-auto size-10 text-muted-foreground" />
        <h1 className="text-headline-md">Sin conexión</h1>
        <p className="text-body-md text-muted-foreground">
          Puede consultar los vencimientos y el libro que ya abrió. Para radicar, corregir o aprobar se necesita
          conexión: nada se guarda a medias.
        </p>
      </div>
    </main>
  );
}
