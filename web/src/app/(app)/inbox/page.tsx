import type { Metadata } from "next";
import { Suspense } from "react";

import { InboxSkeleton, InboxTemplate } from "@/features/inbox";

export const metadata: Metadata = { title: "Bandeja" };

export default function InboxPage({ searchParams }: PageProps<"/inbox">) {
  return (
    <Suspense fallback={<InboxSkeleton />}>
      <InboxTemplate searchParams={searchParams} />
    </Suspense>
  );
}
