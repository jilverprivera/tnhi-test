import { cva, type VariantProps } from "class-variance-authority";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  CircleDot,
  Copy,
  Flame,
  Info,
  ShieldAlert,
  Undo2,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/shared/lib/cn";

/** The one status-to-color mapping (theme-web). Color is never the only signal: icon + label. */
const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-label-sm whitespace-nowrap",
  {
    variants: {
      tone: {
        success: "bg-success-soft text-success-soft-foreground",
        warning: "bg-warning-soft text-warning-soft-foreground",
        danger: "bg-danger-soft text-danger-soft-foreground",
        info: "bg-info-soft text-info-soft-foreground",
        duplicate: "bg-duplicate-soft text-duplicate-soft-foreground",
        primary: "bg-primary-soft text-primary-soft-foreground",
        muted: "bg-muted text-muted-foreground",
      },
    },
    defaultVariants: { tone: "muted" },
  },
);

export type BadgeTone = NonNullable<VariantProps<typeof badgeVariants>["tone"]>;

const TONE_ICON: Record<BadgeTone, LucideIcon> = {
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: ShieldAlert,
  info: Undo2,
  duplicate: Copy,
  primary: CircleDot,
  muted: Ban,
};

export const ICONS = { urgent: Flame, info: Info } as const;

interface StatusBadgeProps {
  tone: BadgeTone;
  label: string;
  icon?: LucideIcon;
  className?: string;
}

export function StatusBadge({ tone, label, icon, className }: StatusBadgeProps) {
  const Icon = icon ?? TONE_ICON[tone];
  return (
    <span className={cn(badgeVariants({ tone }), className)}>
      <Icon aria-hidden className="size-3.5 shrink-0" />
      {label}
    </span>
  );
}
