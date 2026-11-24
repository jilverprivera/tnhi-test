"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

import { Button } from "@/shared/ui/primitives/button";

const NEXT = { light: "dark", dark: "system", system: "light" } as const;
const LABEL = { light: "Tema claro", dark: "Tema oscuro", system: "Tema del sistema" } as const;
const ICON = { light: Sun, dark: Moon, system: Monitor } as const;

const subscribe = () => () => {};

export function ThemeToggle() {
  const { theme = "system", setTheme } = useTheme();
  const mounted = useSyncExternalStore(subscribe, () => true, () => false);
  const current = (mounted ? theme : "system") as keyof typeof NEXT;
  const Icon = ICON[current];
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(NEXT[current])}
      aria-label={`${LABEL[current]}. Cambiar tema`}
      title={LABEL[current]}
    >
      <Icon aria-hidden />
    </Button>
  );
}
