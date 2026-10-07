import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { chatApi } from "./api";

export const chatKeys = {
  threads: ["chat", "threads"] as const,
  messages: (threadId: string) => ["chat", "messages", threadId] as const,
};

export function useChatThreads() {
  return useQuery({ queryKey: chatKeys.threads, queryFn: () => chatApi.threads() });
}

export function useChatMessages(threadId: string) {
  return useQuery({
    queryKey: chatKeys.messages(threadId),
    queryFn: () => chatApi.messages(threadId),
    enabled: threadId.length > 0,
  });
}

export function useDeleteThread() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (threadId: string) => chatApi.deleteThread(threadId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatKeys.threads }),
  });
}