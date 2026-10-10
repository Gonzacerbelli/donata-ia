import type { SaleItem, WorkCard, WorkPriority, WorkStatus } from "@/types/domain";

export const WORK_STATUSES: WorkStatus[] = [
  "pendiente",
  "en_curso",
  "bloqueado",
  "terminado",
];

export const WORK_PRIORITIES: WorkPriority[] = ["alta", "media", "baja"];

export const WORK_STATUS_LABELS: Record<WorkStatus, string> = {
  pendiente: "Pendiente",
  en_curso: "En curso",
  bloqueado: "Bloqueado",
  terminado: "Terminado",
};

export const WORK_PRIORITY_LABELS: Record<WorkPriority, string> = {
  alta: "Alta",
  media: "Media",
  baja: "Baja",
};

export function groupByStatus(cards: WorkCard[]): Record<WorkStatus, WorkCard[]> {
  const grouped: Record<WorkStatus, WorkCard[]> = {
    pendiente: [],
    en_curso: [],
    bloqueado: [],
    terminado: [],
  };
  for (const card of cards) {
    grouped[card.status]?.push(card);
  }
  return grouped;
}

export function summarizeItems(items: SaleItem[]): string {
  const descriptions = items
    .map((item) => item.description)
    .filter((description): description is string => Boolean(description));
  return descriptions.length > 0 ? descriptions.join(", ") : "Sin �tems";
}
