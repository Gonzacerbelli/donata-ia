import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clientsApi } from "./api";
import type { ClientFilters, ClientInput, ClientUpdateInput } from "./types";

export const clientKeys = {
  all: ["clients"] as const,
  list: (filters: ClientFilters) => ["clients", "list", filters] as const,
  sales: (clientId: string) => ["clients", clientId, "sales"] as const,
};

export function useClients(filters: ClientFilters = {}) {
  return useQuery({
    queryKey: clientKeys.list(filters),
    queryFn: () => clientsApi.list(filters),
  });
}

export function useClientSales(clientId: string | null) {
  return useQuery({
    queryKey: clientKeys.sales(clientId ?? ""),
    queryFn: () => clientsApi.sales(clientId ?? ""),
    enabled: Boolean(clientId),
  });
}

export function useCreateClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ClientInput) => clientsApi.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: clientKeys.all }),
  });
}

export function useUpdateClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ClientUpdateInput }) =>
      clientsApi.update(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: clientKeys.all }),
  });
}

export function useDeleteClient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => clientsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: clientKeys.all }),
  });
}