import { cn } from "@/shared/lib/cn";

export function Eyebrow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("text-eyebrow uppercase text-muted-foreground", className)}>{children}</p>;
}
