import { copy } from "@/shared/i18n/es";
import { Logo } from "@/shared/ui/atoms/Logo";

import { LoginForm } from "../organisms/LoginForm";

export function LoginTemplate() {
  return (
    <main className="grid min-h-dvh place-items-center bg-sidebar px-4 py-10">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center gap-3 text-center">
          <Logo className="size-12" />
          <div>
            <h1 className="text-headline-lg">{copy.appName}</h1>
            <p className="text-body-md text-muted-foreground">Radicación asistida · {copy.company}</p>
          </div>
        </div>
        <div className="rounded-2xl border bg-card p-6 shadow-md">
          <LoginForm />
        </div>
        <p className="text-center text-caption text-muted-foreground">
          Nada se reenvía sin su aprobación. Los datos se quedan en los servidores de TAC.
        </p>
      </div>
    </main>
  );
}
