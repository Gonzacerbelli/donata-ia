import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { Client, Sale } from "@/types/domain";

import type { ClientFilters, ClientInput, ClientUpdateInput } from "./types";

export const clientsApi = {
  async list(filters: ClientFilters): Promise<Client[]> {
    const { data } = await api.get<Client[]>(`/clients${toQuery({ ...filters })}`);
    return data;
  },
  async create(input: ClientInput): Promise<Client> {
    const { data } = await api.post<Client>("/clients", input);
    return data;
  },
  async update(id: string, input: ClientUpdateInput): Promise<Client> {
    const { data } = await api.patch<Client>(`/clients/${id}`, input);
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/clients/${id}`);
  },
  async sales(clientId: string): Promise<Sale[]> {
    const { data } = await api.get<Sale[]>(`/sales${toQuery({ client_id: clientId })}`);
    return data;
  },
};