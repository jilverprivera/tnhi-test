import { cn } from "@/shared/lib/cn";

interface FieldRowProps {
  label: string;
  value: React.ReactNode;
  emphasis?: "default" | "danger" | "warning";
  mono?: boolean;
}

export function FieldRow({ label, value, emphasis = "default", mono }: FieldRowProps) {
  return (
    <div className="grid grid-cols-[minmax(0,9rem)_1fr] gap-3 py-2 text-body-sm">
      <dt className="text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "min-w-0 break-words",
          mono && "font-mono text-body-sm font-normal tabular break-all",
          emphasis === "danger" && "font-semibold text-danger",
          emphasis === "warning" && "font-semibold text-warning",
        )}
      >
        {value === "" || value === null || value === undefined ? "—" : value}
      </dd>
    </div>
  );
}
