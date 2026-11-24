import { Skeleton } from "@/shared/ui/primitives/skeleton";

export function SessionSummarySkeleton() {
  return (
    <div className="flex items-center gap-3" aria-hidden>
      <Skeleton className="hidden h-8 w-32 md:block" />
      <Skeleton className="size-9 rounded-full" />
    </div>
  );
}
