import type { Metadata } from "next";
import { Suspense } from "react";

import { ComplianceSkeleton, ComplianceTemplate } from "@/features/compliance";

export const metadata: Metadata = { title: "Cumplimiento" };

export default function CompliancePage({ searchParams }: PageProps<"/compliance">) {
  return (
    <Suspense fallback={<ComplianceSkeleton />}>
      <ComplianceTemplate searchParams={searchParams} />
    </Suspense>
  );
}
