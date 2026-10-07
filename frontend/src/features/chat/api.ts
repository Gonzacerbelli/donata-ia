import { api } from "@/lib/http";
import type { ChatMessage, ChatResponse, ChatThread } from "@/types/domain";

export const chatApi = {
  async send(threadId: string, message: string): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>("/chat", { thread_id: threadId, message });
    return data;
  },
  async threads(): Promise<ChatThread[]> {
    const { data } = await api.get<ChatThread[]>("/chat/threads");
    return data;
  },
  async createThread(threadId: string, title?: string): Promise<ChatThread> {
    const { data } = await api.post<ChatThread>("/chat/threads", { thread_id: threadId, title });
    return data;
  },
  async renameThread(threadId: string, title: string): Promise<ChatThread> {
    const { data } = await api.patch<ChatThread>(`/chat/threads/${threadId}`, { title });
    return data;
  },
  async deleteThread(threadId: string): Promise<void> {
    await api.delete(`/chat/threads/${threadId}`);
  },
  async messages(threadId: string): Promise<ChatMessage[]> {
    const { data } = await api.get<ChatMessage[]>(`/chat/threads/${threadId}/messages`);
    return data;
  },
};