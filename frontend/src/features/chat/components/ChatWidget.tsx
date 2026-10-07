import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { chatApi } from "@/features/chat/api";
import { useChatMessages } from "@/features/chat/hooks";
import { ApiError } from "@/lib/http";
import type { ChatMessage } from "@/types/domain";

const THREAD_KEY = "donata.chat.thread";

function newThreadId(): string {
  return `web-${crypto.randomUUID()}`;
}

function loadThreadId(): string {
  const existing = localStorage.getItem(THREAD_KEY);
  if (existing) return existing;
  const created = newThreadId();
  localStorage.setItem(THREAD_KEY, created);
  return created;
}

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [threadId, setThreadId] = useState(loadThreadId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const history = useChatMessages(threadId);

  useEffect(() => {
    if (history.data) setMessages(history.data);
  }, [history.data]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, pending, open]);

  useEffect(() => {
    if (retryAfter <= 0) return;
    const timer = setInterval(() => setRetryAfter((value) => Math.max(0, value - 1)), 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  const canSend = input.trim().length > 0 && !pending && retryAfter === 0;

  async function handleSend() {
    const text = input.trim();
    if (!text) return;
    setError(null);
    setInput("");
    setPending(true);
    const optimistic: ChatMessage = {
      id: `local-user-${Date.now()}`,
      thread_id: threadId,
      role: "user",
      content: text,
      tool_calls: [],
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    try {
      const response = await chatApi.send(threadId, text);
      setMessages((current) => [
        ...current,
        {
          id: `local-assistant-${Date.now()}`,
          thread_id: response.thread_id,
          role: "assistant",
          content: response.response,
          tool_calls: response.tool_calls,
          created_at: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        if (err.retryAfter) setRetryAfter(err.retryAfter);
      } else {
        setError("El asistente no está disponible en este momento.");
      }
    } finally {
      setPending(false);
    }
  }

  function handleNewConversation() {
    const created = newThreadId();
    localStorage.setItem(THREAD_KEY, created);
    setThreadId(created);
    setMessages([]);
    setError(null);
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      {open && (
        <div className="mb-3 flex h-[32rem] w-80 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-slate-800">Asistente Donata</p>
              <p className="text-xs text-slate-500">Consultas sobre tu negocio</p>
            </div>
            <button
              type="button"
              aria-label="Cerrar asistente"
              className="text-slate-400 hover:text-slate-700"
              onClick={() => setOpen(false)}
            >
              ✕
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
            {history.isLoading ? (
              <div className="flex justify-center py-10">
                <Spinner />
              </div>
            ) : messages.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-500">
                Preguntame por tus ventas, stock o clientes.
              </p>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={message.role === "user" ? "text-right" : "text-left"}
                >
                  <div
                    className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                      message.role === "user"
                        ? "bg-brand-600 text-white"
                        : "bg-slate-100 text-slate-800"
                    }`}
                  >
                    {message.content}
                  </div>
                  {message.tool_calls.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {message.tool_calls.map((call, index) => (
                        <span
                          key={index}
                          className="rounded bg-slate-50 px-2 py-0.5 text-[10px] text-slate-400"
                        >
                          {String((call as { tool?: string }).tool ?? "consulta")}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
            {pending && (
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Spinner />
                Pensando…
              </div>
            )}
          </div>

          {error && (
            <p className="border-t border-red-100 bg-red-50 px-3 py-2 text-xs text-red-600">
              {error}
            </p>
          )}

          <div className="flex items-end gap-2 border-t border-slate-100 p-3">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  if (canSend) void handleSend();
                }
              }}
              rows={2}
              placeholder="Escribí tu consulta..."
              className="flex-1 resize-none rounded-lg border-0 bg-slate-50 px-3 py-2 text-sm text-slate-800 ring-1 ring-inset ring-slate-200 focus:ring-2 focus:ring-brand-600 focus:outline-none"
            />
            <Button size="sm" disabled={!canSend} onClick={() => void handleSend()}>
              Enviar
            </Button>
          </div>
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            handleNewConversation();
            setOpen(true);
          }}
          className="rounded-full bg-white p-2 text-slate-400 shadow-md hover:text-slate-600"
          aria-label="Nueva conversación"
          title="Nueva conversación"
        >
          ✎
        </button>
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="rounded-full bg-brand-600 p-3 text-white shadow-lg hover:bg-brand-700"
          aria-label="Abrir asistente"
        >
          <span aria-hidden="true" className="text-lg leading-none">
            💬
          </span>
        </button>
      </div>
    </div>
  );
}