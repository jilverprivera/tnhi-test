import type { Metadata } from "next";
import { Suspense } from "react";

import { DeadlinesSkeleton, DeadlinesTemplate } from "@/features/deadlines";

export const metadata: Metadata = { title: "Vencimientos" };

export default function DeadlinesPage() {
  return (
    <Suspense fallback={<DeadlinesSkeleton />}>
      <DeadlinesTemplate />
    </Suspense>
  );
}
