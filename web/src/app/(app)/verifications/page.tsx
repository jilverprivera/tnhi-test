import type { Metadata } from "next";
import { Suspense } from "react";

import { VerificationsSkeleton, VerificationsTemplate } from "@/features/verifications";

export const metadata: Metadata = { title: "Por verificar" };

export default function VerificationsPage() {
  return (
    <Suspense fallback={<VerificationsSkeleton />}>
      <VerificationsTemplate />
    </Suspense>
  );
}
