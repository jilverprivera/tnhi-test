import { Inbox } from "lucide-react";

import { EmptyState } from "@/shared/ui/molecules/EmptyState";

import type { InboxItemView } from "../../model/types";
import { InboxRow } from "../molecules/InboxRow";

export function InboxList({ items }: { items: InboxItemView[] }) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="Nada por aquí"
        description="Lea el buzón o suba correos .eml para que el sistema prepare las propuestas."
      />
    );
  }
  return (
    <ul className="space-y-2" aria-label="Documentos">
      {items.map((item) => (
        <InboxRow key={item.id} item={item} />
      ))}
    </ul>
  );
}
