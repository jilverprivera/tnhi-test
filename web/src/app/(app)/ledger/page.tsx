import type { Metadata } from "next";
import { Suspense } from "react";

import { LedgerSkeleton, LedgerTemplate } from "@/features/ledger";

export const metadata: Metadata = { title: "Libro" };

export default function LedgerPage({ searchParams }: PageProps<"/ledger">) {
  return (
    <Suspense fallback={<LedgerSkeleton />}>
      <LedgerTemplate searchParams={searchParams} />
    </Suspense>
  );
}
