import type { Metadata } from "next";
import { Suspense } from "react";

import { SettingsSkeleton, SettingsTemplate } from "@/features/settings";

export const metadata: Metadata = { title: "Ajustes" };

export default function SettingsPage() {
  return (
    <Suspense fallback={<SettingsSkeleton />}>
      <SettingsTemplate />
    </Suspense>
  );
}
