import { cn } from "@/shared/lib/cn";
import type { BadgeTone } from "@/shared/ui/molecules/StatusBadge";

const TONE_TEXT: Record<BadgeTone, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  info: "text-info",
  duplicate: "text-duplicate",
  primary: "text-primary",
  muted: "text-muted-foreground",
};

interface StatTileProps {
  label: string;
  value: number | string;
  hint?: string;
  tone?: BadgeTone;
  className?: string;
}

export function StatTile({ label, value, hint, tone = "muted", className }: StatTileProps) {
  return (
    <div className={cn("rounded-xl border bg-card p-4 shadow-xs", className)}>
      <p className="text-label-sm text-muted-foreground">{label}</p>
      <p className={cn("mt-1 font-display text-headline-lg tabular", TONE_TEXT[tone])}>{value}</p>
      {hint ? <p className="mt-0.5 text-caption text-muted-foreground">{hint}</p> : null}
    </div>
  );
}
