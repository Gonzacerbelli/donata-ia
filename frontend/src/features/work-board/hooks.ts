import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { usersApi, workApi } from "./api";
import type { WorkFilters, WorkUpdateInput } from "./types";

export const workKeys = {
  all: ["work-items"] as const,
  list: (filters: WorkFilters) => ["work-items", "list", filters] as const,
};

export const userKeys = {
  all: ["users"] as const,
};

function invalidateWork(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: workKeys.all });
}

export function useWorkBoard(filters: WorkFilters) {
  return useQuery({
    queryKey: workKeys.list(filters),
    queryFn: () => workApi.list(filters),
  });
}

export function useUpdateWork() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ saleId, input }: { saleId: string; input: WorkUpdateInput }) =>
      workApi.update(saleId, input),
    onSuccess: () => invalidateWork(queryClient),
  });
}

export function useAddComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ saleId, text }: { saleId: string; text: string }) =>
      workApi.addComment(saleId, text),
    onSuccess: () => invalidateWork(queryClient),
  });
}

export function useUsers() {
  return useQuery({ queryKey: userKeys.all, queryFn: () => usersApi.list() });
}
