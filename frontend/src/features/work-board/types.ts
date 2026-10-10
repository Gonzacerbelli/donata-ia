import type { WorkPriority, WorkStatus } from "@/types/domain";

export interface WorkFilters {
  status?: string;
  priority?: string;
  assigned_to?: string;
  date_sort?: string;
}

export interface WorkUpdateInput {
  status?: WorkStatus;
  priority?: WorkPriority;
  assigned_to?: string | null;
}
