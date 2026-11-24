import { Flame } from "lucide-react";

import { presentationLabel } from "@/shared/i18n/es";
import { StatusBadge } from "@/shared/ui/molecules/StatusBadge";

export function UrgentBadge() {
  return <StatusBadge tone="danger" label={presentationLabel.urgent} icon={Flame} />;
}
