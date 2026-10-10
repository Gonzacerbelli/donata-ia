import { useDraggable } from "@dnd-kit/core";

import { formatCurrency, formatDate } from "@/lib/format";
import type { WorkCard as WorkCardModel, WorkPriority } from "@/types/domain";

import { WORK_PRIORITIES, WORK_PRIORITY_LABELS, summarizeItems } from "../lib";
import { AssigneeSelect } from "./AssigneeSelect";
import { PriorityBadge } from "./PriorityBadge";

interface WorkCardProps {
  card: WorkCardModel;
  disabled?: boolean;
  onPriorityChange: (priority: WorkPriority) => void;
  onAssigneeChange: (assignedTo: string | null) => void;
  onOpenComments: () => void;
}

export function WorkCard({
  card,
  disabled,
  onPriorityChange,
  onAssigneeChange,
  onOpenComments,
}: WorkCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.sale_id,
  });

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      data-testid={`work-card-${card.sale_id}`}
      className={`rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition-shadow hover:shadow-md ${
        isDragging ? "opacity-60" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs text-slate-500">{formatDate(card.date)}</span>
        <button
          type="button"
          aria-label="Mover tarjeta"
          className="cursor-grab rounded p-1 leading-none text-slate-400 hover:bg-slate-100"
          {...listeners}
          {...attributes}
        >
          ?
        </button>
      </div>

      <p className="mt-1 line-clamp-2 text-sm font-medium text-slate-800">
        {summarizeItems(card.items)}
      </p>

      <div className="mt-2 flex items-center justify-between">
        <PriorityBadge priority={card.priority} />
        <span className="text-sm font-medium text-slate-700">{formatCurrency(card.total)}</span>
      </div>

      <div className="mt-2 flex flex-col gap-2">
        <AssigneeSelect
          value={card.assigned_to}
          disabled={disabled}
          onChange={onAssigneeChange}
        />
        <select
          aria-label="Prioridad"
          value={card.priority}
          disabled={disabled}
          onChange={(event) => onPriorityChange(event.target.value as WorkPriority)}
          className="rounded-lg bg-white px-3 py-2 text-sm text-slate-900 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          {WORK_PRIORITIES.map((priority) => (
            <option key={priority} value={priority}>
              {WORK_PRIORITY_LABELS[priority]}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        onClick={onOpenComments}
        className="mt-2 text-sm font-medium text-brand-600 hover:underline"
      >
        Comentarios ({card.comments.length})
      </button>
    </div>
  );
}
