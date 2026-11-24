import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function LedgerSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando libro">
      <Skeleton className="h-16 w-1/2" />
      <Skeleton className="h-11 w-full" />
      <Skeleton className="h-[60dvh] w-full rounded-xl" />
    </div>
  );
}
