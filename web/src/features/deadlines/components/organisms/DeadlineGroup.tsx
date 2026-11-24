import type { DeadlineView } from "../../model/types";
import { DeadlineCard } from "../molecules/DeadlineCard";

export function DeadlineGroup({ title, items, empty }: { title: string; items: DeadlineView[]; empty: string }) {
  return (
    <section aria-labelledby={`group-${title}`} className="space-y-3 break-inside-avoid">
      <h2 id={`group-${title}`} className="text-headline-md">
        {title} <span className="text-muted-foreground tabular">({items.length})</span>
      </h2>
      {items.length ? (
        <ul className="space-y-2">
          {items.map((d) => (
            <DeadlineCard key={d.key} deadline={d} />
          ))}
        </ul>
      ) : (
        <p className="rounded-xl border border-dashed p-4 text-body-sm text-muted-foreground">{empty}</p>
      )}
    </section>
  );
}
