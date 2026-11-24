import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function DeadlinesSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Cargando vencimientos">
      <Skeleton className="h-16 w-1/2" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}
