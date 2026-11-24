"use client";

import { AlertTriangle, LogIn, RotateCcw } from "lucide-react";

// The barrel also exports Server Components (they read cookies): import the action module directly.
import { logoutAction } from "@/features/session/api/session-actions";
import { Button } from "@/shared/ui/primitives/button";

/** A page could not load (API down or session expired): offer the two ways out. */
export default function AppError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div role="alert" className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center">
      <span className="grid size-12 place-items-center rounded-full bg-warning-soft text-warning-soft-foreground">
        <AlertTriangle aria-hidden className="size-6" />
      </span>
      <div className="space-y-1">
        <h1 className="text-headline-md">No se pudo cargar esta vista</h1>
        <p className="text-body-sm text-muted-foreground">
          Puede ser una falla momentánea del servidor o que su sesión haya expirado. Nada de lo que aprobó se perdió.
        </p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button onClick={reset}>
          <RotateCcw aria-hidden /> Reintentar
        </Button>
        <form action={logoutAction}>
          <Button type="submit" variant="outline" className="w-full">
            <LogIn aria-hidden /> Ingresar de nuevo
          </Button>
        </form>
      </div>
    </div>
  );
}
