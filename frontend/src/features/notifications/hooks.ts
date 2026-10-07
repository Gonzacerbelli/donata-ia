import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { notificationsApi, type NotificationUpdateInput } from "./api";
import type { NotificationList } from "@/types/domain";

const NOTIFICATIONS_KEY = ["notifications"] as const;

export function useNotifications() {
  return useQuery({
    queryKey: NOTIFICATIONS_KEY,
    queryFn: () => notificationsApi.list(),
    refetchInterval: 60_000,
  });
}

function applyResult(queryClient: ReturnType<typeof useQueryClient>, result: NotificationList) {
  queryClient.setQueryData(NOTIFICATIONS_KEY, result);
}

export function useUpdateNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: NotificationUpdateInput }) =>
      notificationsApi.update(id, body),
    onSuccess: (result) => applyResult(queryClient, result),
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsApi.readAll(),
    onSuccess: (result) => applyResult(queryClient, result),
  });
}

export function useDismissAll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsApi.dismissAll(),
    onSuccess: (result) => applyResult(queryClient, result),
  });
}