import type { WorkPriority } from "@/types/domain";

import { WORK_PRIORITY_LABELS } from "../lib";

const priorityColors: Record<WorkPriority, string> = {
  alta: "bg-red-50 text-red-600",
  media: "bg-amber-50 text-amber-600",
  baja: "bg-slate-100 text-slate-600",
};

export function PriorityBadge({ priority }: { priority: WorkPriority }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${priorityColors[priority]}`}>
      {WORK_PRIORITY_LABELS[priority]}
    </span>
  );
}
