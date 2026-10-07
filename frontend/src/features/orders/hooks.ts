import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { productKeys } from "@/features/products/hooks";

import { salesApi, type SaleCreatePayload } from "./api";
import type { PaymentInput, SaleFilters, SaleUpdateInput } from "./types";

export const saleKeys = {
  all: ["sales"] as const,
  list: (filters: SaleFilters) => ["sales", "list", filters] as const,
  detail: (id: string) => ["sales", "detail", id] as const,
};

function invalidateSales(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: saleKeys.all });
  queryClient.invalidateQueries({ queryKey: productKeys.all });
}

export function useSales(filters: SaleFilters) {
  return useQuery({
    queryKey: saleKeys.list(filters),
    queryFn: () => salesApi.list(filters),
  });
}

export function useSale(id: string | undefined) {
  return useQuery({
    queryKey: saleKeys.detail(id ?? ""),
    queryFn: () => salesApi.get(id ?? ""),
    enabled: Boolean(id),
  });
}

export function useCreateSale() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SaleCreatePayload) => salesApi.create(payload),
    onSuccess: () => invalidateSales(queryClient),
  });
}

export function useUpdateSale(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SaleUpdateInput) => salesApi.update(id, input),
    onSuccess: () => invalidateSales(queryClient),
  });
}

export function useDeleteSale() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => salesApi.remove(id),
    onSuccess: () => invalidateSales(queryClient),
  });
}

export function useAddPayment(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PaymentInput) => salesApi.addPayment(id, input),
    onSuccess: () => invalidateSales(queryClient),
  });
}