import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { Sale } from "@/types/domain";

import type { PaymentInput, SaleFilters, SaleUpdateInput } from "./types";

export interface SaleCreatePayload {
  client_id: string;
  client_type?: string;
  date?: string;
  items: Array<{ product_id?: string; description?: string; qty: number; unit_price?: number }>;
  shipping_cost?: number;
  discount?: number;
  discount_pct?: number;
  notes?: string;
  ship_by?: string;
  payment_due?: string;
}

export const salesApi = {
  async list(filters: SaleFilters): Promise<Sale[]> {
    const { data } = await api.get<Sale[]>(`/sales${toQuery({ ...filters })}`);
    return data;
  },
  async get(id: string): Promise<Sale> {
    const { data } = await api.get<Sale>(`/sales/${id}`);
    return data;
  },
  async create(payload: SaleCreatePayload): Promise<Sale> {
    const { data } = await api.post<Sale>("/sales", payload);
    return data;
  },
  async update(id: string, input: SaleUpdateInput): Promise<Sale> {
    const { data } = await api.patch<Sale>(`/sales/${id}`, input);
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/sales/${id}`);
  },
  async addPayment(id: string, input: PaymentInput): Promise<Sale> {
    const { data } = await api.post<Sale>(`/sales/${id}/payments`, input);
    return data;
  },
};