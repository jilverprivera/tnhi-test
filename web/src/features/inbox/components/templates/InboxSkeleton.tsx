import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function InboxSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando bandeja">
      <Skeleton className="h-16 w-2/3" />
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <div className="space-y-2">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-20 rounded-xl" />
        ))}
      </div>
    </div>
  );
}
