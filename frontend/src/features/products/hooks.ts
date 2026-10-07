import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { productsApi } from "./api";
import type { ProductFilters, ProductInput, ProductUpdateInput, StockAdjustInput } from "./types";

export const productKeys = {
  all: ["products"] as const,
  list: (filters: ProductFilters) => ["products", "list", filters] as const,
  moves: (productId: string) => ["products", productId, "moves"] as const,
};

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: productKeys.list(filters),
    queryFn: () => productsApi.list(filters),
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProductInput) => productsApi.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productKeys.all }),
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ProductUpdateInput }) =>
      productsApi.update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productKeys.all }),
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => productsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productKeys.all }),
  });
}

export function useAdjustStock() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StockAdjustInput) => productsApi.adjustStock(input),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: productKeys.all });
      queryClient.invalidateQueries({ queryKey: productKeys.moves(variables.product_id) });
    },
  });
}

export function useProductMoves(productId: string | null) {
  return useQuery({
    queryKey: productKeys.moves(productId ?? ""),
    queryFn: () => productsApi.moves(productId ?? ""),
    enabled: Boolean(productId),
  });
}