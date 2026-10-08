import { chatApi } from "./api";

export const THREAD_KEY = "donata.chat.thread";

export function newThreadId(): string {
  return `web-${crypto.randomUUID()}`;
}

export function loadThreadId(): string | null {
  return localStorage.getItem(THREAD_KEY);
}

export function saveThreadId(threadId: string): void {
  localStorage.setItem(THREAD_KEY, threadId);
}

export async function resolveThreadId(): Promise<string> {
  const stored = loadThreadId();
  try {
    const threads = await chatApi.threads();
    if (stored && threads.some((thread) => thread.thread_id === stored)) return stored;
    return threads[0]?.thread_id ?? newThreadId();
  } catch {
    return stored ?? newThreadId();
  }
}
