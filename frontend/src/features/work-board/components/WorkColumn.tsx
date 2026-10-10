import { useDroppable } from "@dnd-kit/core";

import type { WorkCard as WorkCardModel, WorkPriority, WorkStatus } from "@/types/domain";

import { WORK_STATUS_LABELS } from "../lib";
import { WorkCard } from "./WorkCard";

interface WorkColumnProps {
  status: WorkStatus;
  cards: WorkCardModel[];
  onPriorityChange: (card: WorkCardModel, priority: WorkPriority) => void;
  onAssigneeChange: (card: WorkCardModel, assignedTo: string | null) => void;
  onOpenComments: (card: WorkCardModel) => void;
}

export function WorkColumn({
  status,
  cards,
  onPriorityChange,
  onAssigneeChange,
  onOpenComments,
}: WorkColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <section
      ref={setNodeRef}
      aria-label={WORK_STATUS_LABELS[status]}
      data-testid={`work-column-${status}`}
      className={`flex flex-col gap-3 rounded-2xl border p-3 transition-colors ${
        isOver ? "border-brand-400 bg-brand-50/40" : "border-slate-200 bg-slate-50"
      }`}
    >
      <header className="flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold text-slate-700">{WORK_STATUS_LABELS[status]}</h2>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-500">
          {cards.length}
        </span>
      </header>

      <div className="flex min-h-24 flex-col gap-3">
        {cards.length === 0 && (
          <p className="px-1 py-6 text-center text-xs text-slate-400">Sin tarjetas</p>
        )}
        {cards.map((card) => (
          <WorkCard
            key={card.sale_id}
            card={card}
            onPriorityChange={(priority) => onPriorityChange(card, priority)}
            onAssigneeChange={(assignedTo) => onAssigneeChange(card, assignedTo)}
            onOpenComments={() => onOpenComments(card)}
          />
        ))}
      </div>
    </section>
  );
}
