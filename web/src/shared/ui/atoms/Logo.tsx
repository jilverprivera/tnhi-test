import { cn } from "@/shared/lib/cn";

/** Docket mark: a stamped folder tab. Decorative unless a label is given. */
export function Logo({ className, label }: { className?: string; label?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("size-8", className)}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <rect x="2" y="6" width="28" height="22" rx="6" className="fill-primary" />
      <path d="M2 12a6 6 0 0 1 6-6h7l3 4h8a6 6 0 0 1 6 6" className="fill-primary-hover" />
      <path d="M10 19.5l4 4 8-9" fill="none" strokeWidth="2.75" strokeLinecap="round" strokeLinejoin="round" className="stroke-primary-foreground" />
    </svg>
  );
}
