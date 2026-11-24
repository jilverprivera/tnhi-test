import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed bg-card/50 px-6 py-12 text-center">
      <span className="grid size-12 place-items-center rounded-full bg-primary-soft text-primary-soft-foreground">
        <Icon aria-hidden className="size-6" />
      </span>
      <div className="max-w-sm space-y-1">
        <p className="text-headline-sm">{title}</p>
        {description ? <p className="text-body-sm text-muted-foreground">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
