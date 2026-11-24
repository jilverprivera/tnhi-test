"use client";

import { LogOut } from "lucide-react";

import { Button } from "@/shared/ui/primitives/button";

/** Clears the offline copies (ledger, deadlines: they hold NITs and amounts) before signing out. */
export function LogoutButton({ action }: { action: () => Promise<void> }) {
  async function clearOfflineCopies() {
    if (!("caches" in window)) return;
    const names = await caches.keys();
    await Promise.all(names.filter((n) => n.startsWith("docket-read-views")).map((n) => caches.delete(n)));
  }
  return (
    <form action={action} onSubmit={() => void clearOfflineCopies()}>
      <Button variant="ghost" size="icon" type="submit" aria-label="Cerrar sesión" title="Cerrar sesión">
        <LogOut aria-hidden />
      </Button>
    </form>
  );
}
