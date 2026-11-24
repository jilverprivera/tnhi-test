import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function DocumentReviewSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando documento">
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-20 w-3/4" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[60dvh] rounded-xl" />
        <div className="space-y-4">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
