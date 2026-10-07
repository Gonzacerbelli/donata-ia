import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { providersApi } from "./api";
import type { ProviderFilters, ProviderInput, ProviderUpdateInput } from "./types";

export const providerKeys = {
  all: ["providers"] as const,
  list: (filters: ProviderFilters) => ["providers", "list", filters] as const,
};

export function useProviders(filters: ProviderFilters) {
  return useQuery({
    queryKey: providerKeys.list(filters),
    queryFn: () => providersApi.list(filters),
  });
}

export function useCreateProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProviderInput) => providersApi.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: providerKeys.all }),
  });
}

export function useUpdateProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ProviderUpdateInput }) =>
      providersApi.update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: providerKeys.all }),
  });
}

export function useDeleteProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => providersApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: providerKeys.all }),
  });
}