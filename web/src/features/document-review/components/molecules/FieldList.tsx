import { FieldRow } from "@/shared/ui/molecules/FieldRow";

import type { FieldView } from "../../model/types";

export function FieldList({ fields }: { fields: FieldView[] }) {
  return (
    <dl className="divide-y">
      {fields.map((f) => (
        <FieldRow key={f.label} label={f.label} value={f.value} emphasis={f.emphasis} mono={f.isMono} />
      ))}
    </dl>
  );
}
