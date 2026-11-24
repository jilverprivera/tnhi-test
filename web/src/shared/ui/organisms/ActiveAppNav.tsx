"use client";

import { usePathname } from "next/navigation";

import { AppNav, type NavKey } from "@/shared/ui/organisms/AppNav";

export function ActiveAppNav({ variant, items }: { variant: "sidebar" | "tabbar"; items: NavKey[] }) {
  return <AppNav variant={variant} items={items} pathname={usePathname()} />;
}
