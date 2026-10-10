import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { UserSummary, WorkCard } from "@/types/domain";

import type { WorkFilters, WorkUpdateInput } from "./types";

export const workApi = {
  async list(filters: WorkFilters): Promise<WorkCard[]> {
    const { data } = await api.get<WorkCard[]>(`/work-items${toQuery({ ...filters })}`);
    return data;
  },
  async update(saleId: string, input: WorkUpdateInput): Promise<WorkCard> {
    const { data } = await api.patch<WorkCard>(`/work-items/${saleId}`, input);
    return data;
  },
  async addComment(saleId: string, text: string): Promise<WorkCard> {
    const { data } = await api.post<WorkCard>(`/work-items/${saleId}/comments`, { text });
    return data;
  },
};

export const usersApi = {
  async list(): Promise<UserSummary[]> {
    const { data } = await api.get<UserSummary[]>("/users");
    return data;
  },
};
