import { useMemo, useState } from "react";
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";

import { PageHeader } from "@/components/common/PageHeader";
import { Spinner } from "@/components/ui/Spinner";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import type { WorkCard as WorkCardModel, WorkPriority, WorkStatus } from "@/types/domain";

import { useUpdateWork, useUsers, useWorkBoard } from "../hooks";
import {
  WORK_PRIORITIES,
  WORK_PRIORITY_LABELS,
  WORK_STATUSES,
  groupByStatus,
} from "../lib";
import { CommentModal } from "./CommentModal";
import { WorkColumn } from "./WorkColumn";

export function WorkBoardPage() {
  const { get, setParam } = useUrlFilters({ sort: "desc" });
  const sort = get("sort");
  const priority = get("priority");
  const assigned = get("assigned");

  const { data, isLoading, error, refetch } = useWorkBoard({
    date_sort: sort,
    priority,
    assigned_to: assigned,
  });
  const { data: users } = useUsers();
  const updateWork = useUpdateWork();
  const [commentCardId, setCommentCardId] = useState<string | null>(null);

  const cards = useMemo(() => data ?? [], [data]);
  const grouped = useMemo(() => groupByStatus(cards), [cards]);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  const commentCard = cards.find((card) => card.sale_id === commentCardId) ?? null;

  const onDragEnd = (event: DragEndEvent) => {
    const saleId = String(event.active.id);
    const target = event.over?.id;
    if (!target || typeof target !== "string") return;
    const card = cards.find((item) => item.sale_id === saleId);
    if (!card || card.status === target) return;
    updateWork.mutate({ saleId, input: { status: target as WorkStatus } });
  };

  const changePriority = (card: WorkCardModel, value: WorkPriority) => {
    updateWork.mutate({ saleId: card.sale_id, input: { priority: value } });
  };

  const changeAssignee = (card: WorkCardModel, value: string | null) => {
    updateWork.mutate({ saleId: card.sale_id, input: { assigned_to: value } });
  };

  return (
    <div>
      <PageHeader title="Trabajo" description="Tablero de órdenes por estado de trabajo." />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          aria-label="Orden por fecha"
          value={sort}
          onChange={(event) => setParam("sort", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="desc">Más recientes primero</option>
          <option value="asc">Más antiguas primero</option>
        </select>
        <select
          aria-label="Filtrar por prioridad"
          value={priority}
          onChange={(event) => setParam("priority", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todas las prioridades</option>
          {WORK_PRIORITIES.map((value) => (
            <option key={value} value={value}>
              {WORK_PRIORITY_LABELS[value]}
            </option>
          ))}
        </select>
        <select
          aria-label="Filtrar por asignado"
          value={assigned}
          onChange={(event) => setParam("assigned", event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm text-slate-700 ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-brand-600 focus:outline-none"
        >
          <option value="">Todos los asignados</option>
          {(users ?? []).map((user) => (
            <option key={user.id} value={user.id}>
              {user.name ?? user.email ?? "Usuario"}
            </option>
          ))}
        </select>
      </div>

      {isLoading && (
        <div className="flex justify-center rounded-xl border border-slate-200 bg-white py-16">
          <Spinner />
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-white py-16">
          <p className="text-sm text-red-600">{error.message}</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="text-sm font-medium text-brand-600 hover:underline"
          >
            Reintentar
          </button>
        </div>
      )}

      {!isLoading && !error && cards.length === 0 && (
        <div className="flex flex-col items-center gap-2 rounded-xl border border-slate-200 bg-white py-16 text-center">
          <p className="text-sm font-medium text-slate-700">No hay tarjetas</p>
          <p className="text-sm text-slate-500">
            No hay órdenes que coincidan con los filtros seleccionados.
          </p>
        </div>
      )}

      {!isLoading && !error && cards.length > 0 && (
        <DndContext sensors={sensors} onDragEnd={onDragEnd}>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {WORK_STATUSES.map((status) => (
              <WorkColumn
                key={status}
                status={status}
                cards={grouped[status]}
                onPriorityChange={changePriority}
                onAssigneeChange={changeAssignee}
                onOpenComments={(card) => setCommentCardId(card.sale_id)}
              />
            ))}
          </div>
        </DndContext>
      )}

      <CommentModal
        card={commentCard}
        open={Boolean(commentCard)}
        onClose={() => setCommentCardId(null)}
      />
    </div>
  );
}
