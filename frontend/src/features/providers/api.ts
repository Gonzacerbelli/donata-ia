import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { Provider } from "@/types/domain";

import type { ProviderFilters, ProviderInput, ProviderUpdateInput } from "./types";

export const providersApi = {
  async list(filters: ProviderFilters): Promise<Provider[]> {
    const { data } = await api.get<Provider[]>(`/providers${toQuery({ ...filters })}`);
    return data;
  },
  async create(input: ProviderInput): Promise<Provider> {
    const { data } = await api.post<Provider>("/providers", input);
    return data;
  },
  async update(id: string, input: ProviderUpdateInput): Promise<Provider> {
    const { data } = await api.patch<Provider>(`/providers/${id}`, input);
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/providers/${id}`);
  },
};