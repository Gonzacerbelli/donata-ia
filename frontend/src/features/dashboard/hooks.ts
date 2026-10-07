import { useQuery } from "@tanstack/react-query";

import { reportsApi, type ReportRange } from "./api";

export const reportKeys = {
  summary: (range: ReportRange) => ["reports", "summary", range] as const,
  topProducts: (range: ReportRange) => ["reports", "top-products", range] as const,
  lowStock: ["reports", "low-stock"] as const,
  inventoryValue: ["reports", "inventory-value"] as const,
};

export function useSalesSummary(range: ReportRange) {
  return useQuery({
    queryKey: reportKeys.summary(range),
    queryFn: () => reportsApi.summary(range),
  });
}

export function useTopProducts(range: ReportRange, limit = 5) {
  return useQuery({
    queryKey: reportKeys.topProducts(range),
    queryFn: () => reportsApi.topProducts(range, limit),
  });
}

export function useLowStock() {
  return useQuery({ queryKey: reportKeys.lowStock, queryFn: () => reportsApi.lowStock() });
}

export function useInventoryValue() {
  return useQuery({
    queryKey: reportKeys.inventoryValue,
    queryFn: () => reportsApi.inventoryValue(),
  });
}