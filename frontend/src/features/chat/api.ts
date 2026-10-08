import { createSseParser } from "@/features/chat/sse";
import { ApiError, api } from "@/lib/http";
import { tokenStore } from "@/lib/token";
import type { ChatMessage, ChatResponse, ChatStreamEvent, ChatThread } from "@/types/domain";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const chatApi = {
  async send(threadId: string, message: string): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>("/chat", { thread_id: threadId, message });
    return data;
  },
  async *stream(
    threadId: string,
    message: string,
    signal?: AbortSignal,
  ): AsyncGenerator<ChatStreamEvent> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = tokenStore.get();
    if (token) headers.Authorization = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify({ thread_id: threadId, message }),
      signal,
    });

    if (!response.ok) {
      let detail: string | undefined;
      try {
        detail = ((await response.json()) as { detail?: string }).detail;
      } catch {
        detail = undefined;
      }
      const retryAfterHeader = response.headers.get("Retry-After");
      const retryAfter = Number(retryAfterHeader);
      throw new ApiError(
        detail ?? "No pudimos conectar con el servidor.",
        response.status,
        Number.isFinite(retryAfter) ? retryAfter : undefined,
      );
    }

    if (!response.body) {
      throw new ApiError("El navegador no soporta streaming.", 0);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const parse = createSseParser();
    for (;;) {
      const chunk = await reader.read();
      if (chunk.done) break;
      const events = parse(decoder.decode(chunk.value, { stream: true }));
      for (const event of events) yield event;
    }
    for (const event of parse(decoder.decode())) yield event;
  },
  async confirm(threadId: string, token: string): Promise<ChatResponse> {
    const { data } = await api.post<ChatResponse>("/chat/confirm", {
      thread_id: threadId,
      token,
    });
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