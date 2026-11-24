import type { Metadata } from "next";

import { LoginTemplate } from "@/features/session";

export const metadata: Metadata = { title: "Ingresar" };

export default function LoginPage() {
  return <LoginTemplate />;
}
