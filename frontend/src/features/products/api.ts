import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { Product, StockMove } from "@/types/domain";

import type { ProductFilters, ProductInput, ProductUpdateInput, StockAdjustInput } from "./types";

export const productsApi = {
  async list(filters: ProductFilters): Promise<Product[]> {
    const { data } = await api.get<Product[]>(`/products${toQuery({ ...filters })}`);
    return data;
  },
  async create(input: ProductInput): Promise<Product> {
    const { data } = await api.post<Product>("/products", input);
    return data;
  },
  async update(id: string, input: ProductUpdateInput): Promise<Product> {
    const { data } = await api.patch<Product>(`/products/${id}`, input);
    return data;
  },
  async remove(id: string): Promise<void> {
    await api.delete(`/products/${id}`);
  },
  async adjustStock(input: StockAdjustInput): Promise<Product> {
    const { data } = await api.post<Product>("/products/stock/adjust", input);
    return data;
  },
  async moves(productId: string, limit = 50): Promise<StockMove[]> {
    const { data } = await api.get<StockMove[]>(`/products/${productId}/moves${toQuery({ limit })}`);
    return data;
  },
};