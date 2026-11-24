"use client";

import { KeyRound, Loader2 } from "lucide-react";
import { useActionState, useState } from "react";

import { describeError } from "@/shared/i18n/es";
import type { Role } from "@/shared/lib/api-types";
import { cn } from "@/shared/lib/cn";
import { Button } from "@/shared/ui/primitives/button";
import { Input } from "@/shared/ui/primitives/input";
import { Label } from "@/shared/ui/primitives/label";

import { loginAction, type LoginState } from "../../api/session-actions";

const ROLES: { role: Role; title: string; who: string }[] = [
  { role: "CLERK", title: "Radicación", who: "Martha Rojas · radica, corrige y aprueba" },
  { role: "COORDINATOR", title: "Coordinación", who: "Dra. Claudia Herrera · consulta y vencimientos" },
];

/** Demo access codes to offer as a hint, only when the deployment sets them (DOCKET_DEMO_*_CODE). */
export type DemoCodes = Partial<Record<Role, string>>;

export function LoginForm({ demoCodes }: { demoCodes: DemoCodes }) {
  const [state, formAction, isPending] = useActionState<LoginState, FormData>(loginAction, {});
  const [role, setRole] = useState<Role>("CLERK");
  const [code, setCode] = useState("");
  const demoCode = demoCodes[role];

  return (
    <form action={formAction} className="space-y-6">
      <fieldset className="space-y-2">
        <legend className="mb-2 text-label-md">¿Quién ingresa?</legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {ROLES.map((r) => (
            <label
              key={r.role}
              className={cn(
                "flex min-h-16 cursor-pointer flex-col justify-center rounded-xl border bg-card px-4 py-3 transition-colors active:scale-[0.99]",
                role === r.role ? "border-primary bg-primary-soft" : "hover:bg-accent",
              )}
            >
              <input
                type="radio"
                name="role"
                value={r.role}
                checked={role === r.role}
                onChange={() => setRole(r.role)}
                className="sr-only"
              />
              <span className="text-label-md">{r.title}</span>
              <span className="text-caption text-muted-foreground">{r.who}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="space-y-2">
        <Label htmlFor="accessCode">Código de acceso</Label>
        <Input
          id="accessCode"
          name="accessCode"
          type="password"
          autoComplete="current-password"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          aria-invalid={state.errorCode ? true : undefined}
          aria-describedby={state.errorCode ? "login-error" : demoCode ? "login-hint" : undefined}
          className="h-11"
        />
        {state.errorCode ? (
          <p id="login-error" role="alert" className="text-body-sm text-danger">
            {describeError(state.errorCode)}
          </p>
        ) : demoCode ? (
          <p id="login-hint" className="text-caption text-muted-foreground">
            Demostración:{" "}
            <button type="button" className="font-mono underline underline-offset-2" onClick={() => setCode(demoCode)}>
              {demoCode}
            </button>
          </p>
        ) : null}
      </div>

      <Button type="submit" className="h-11 w-full" disabled={isPending}>
        {isPending ? <Loader2 aria-hidden className="animate-spin" /> : <KeyRound aria-hidden />}
        Ingresar
      </Button>
    </form>
  );
}
