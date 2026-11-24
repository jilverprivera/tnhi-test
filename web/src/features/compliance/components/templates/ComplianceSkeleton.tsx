import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function ComplianceSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Cargando cumplimiento">
      <Skeleton className="h-16 w-1/2" />
      <Skeleton className="h-64 rounded-xl" />
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}
