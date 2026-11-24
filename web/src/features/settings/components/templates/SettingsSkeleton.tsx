import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function SettingsSkeleton() {
  return (
    <div className="space-y-8" aria-busy="true" aria-label="Cargando ajustes">
      <Skeleton className="h-16 w-1/2" />
      <Skeleton className="h-24 rounded-xl" />
      <Skeleton className="h-72 rounded-xl" />
    </div>
  );
}
