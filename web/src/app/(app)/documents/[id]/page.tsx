import type { Metadata } from "next";
import { Suspense } from "react";

import { DocumentReviewSkeleton, DocumentReviewTemplate } from "@/features/document-review";

export const metadata: Metadata = { title: "Revisar documento" };

export default function DocumentPage({ params }: PageProps<"/documents/[id]">) {
  return (
    <Suspense fallback={<DocumentReviewSkeleton />}>
      <DocumentReviewTemplate params={params} />
    </Suspense>
  );
}
