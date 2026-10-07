import { toQuery } from "@/lib/api/query";
import { api } from "@/lib/http";
import type { InventoryValue, Product, SalesSummary, TopProduct } from "@/types/domain";

export interface ReportRange {
  date_from?: string;
  date_to?: string;
}

export const reportsApi = {
  async summary(range: ReportRange): Promise<SalesSummary> {
    const { data } = await api.get<SalesSummary>(`/reports/summary${toQuery({ ...range })}`);
    return data;
  },
  async topProducts(range: ReportRange, limit = 5): Promise<TopProduct[]> {
    const { data } = await api.get<TopProduct[]>(
      `/reports/top-products${toQuery({ ...range, limit })}`,
    );
    return data;
  },
  async lowStock(): Promise<Product[]> {
    const { data } = await api.get<Product[]>("/reports/low-stock");
    return data;
  },
  async inventoryValue(): Promise<InventoryValue> {
    const { data } = await api.get<InventoryValue>("/reports/inventory-value");
    return data;
  },
};