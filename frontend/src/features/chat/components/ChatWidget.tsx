import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { chatApi } from "@/features/chat/api";
import { chatKeys, useChatMessages } from "@/features/chat/hooks";
import { SIZE_KEY, clampSize, parseSize, type WidgetSize } from "@/features/chat/size";
import { newThreadId, resolveThreadId, saveThreadId } from "@/features/chat/thread";
import { ApiError } from "@/lib/http";
import type { ChatMessage, ChatResponse, PendingAction } from "@/types/domain";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [threadId, setThreadId] = useState("");
  const [ready, setReady] = useState(false);
  const threadRef = useRef("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();
  const [size, setSize] = useState<WidgetSize>(() =>
    parseSize(localStorage.getItem(SIZE_KEY), {
      width: window.innerWidth,
      height: window.innerHeight,
    }),
  );
  const resizeRef = useRef<{ x: number; y: number; width: number; height: number } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const history = useChatMessages(threadId);

  const adoptThread = useCallback((id: string) => {
    threadRef.current = id;
    saveThreadId(id);
    setThreadId(id);
  }, []);

  useEffect(() => {
    let cancelled = false;
    void resolveThreadId().then((id) => {
      if (cancelled) return;
      if (!threadRef.current) adoptThread(id);
      setReady(true);
    });
    return () => {
      cancelled = true;
    };
  }, [adoptThread]);

  useEffect(() => {
    localStorage.setItem(SIZE_KEY, JSON.stringify(size));
  }, [size]);

  useEffect(() => {
    if (history.data) setMessages(history.data);
  }, [history.data]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      abortRef.current = null;
    };
  }, [threadId, open]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, pending, open]);

  useEffect(() => {
    if (retryAfter <= 0) return;
    const timer = setInterval(() => setRetryAfter((value) => Math.max(0, value - 1)), 1000);
    return () => clearInterval(timer);
  }, [retryAfter]);

  const canSend = ready && input.trim().length > 0 && !pending && retryAfter === 0;

  function appendAssistant(response: {
    thread_id: string;
    response: string;
    tool_calls: Record<string, unknown>[];
  }) {
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
  }

  function handleFailure(err: unknown) {
    if (err instanceof ApiError) {
      setError(err.message);
      if (err.retryAfter) setRetryAfter(err.retryAfter);
    } else {
      setError("El asistente no está disponible en este momento.");
    }
  }

  async function handleConfirm() {
    if (!pendingAction) return;
    setError(null);
    setPending(true);
    try {
      const response = await chatApi.confirm(threadId, pendingAction.token);
      setPendingAction(null);
      appendAssistant(response);
    } catch (err) {
      handleFailure(err);
    } finally {
      setPending(false);
    }
  }

  function handleCancelAction() {
    setPendingAction(null);
    setMessages((current) => [
      ...current,
      {
        id: `local-cancel-${Date.now()}`,
        thread_id: threadId,
        role: "assistant",
        content: "Acción cancelada. No se modificó nada.",
        tool_calls: [],
        created_at: new Date().toISOString(),
      },
    ]);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text) return;
    setError(null);
    setPendingAction(null);
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
    const controller = new AbortController();
    abortRef.current = controller;
    let final: ChatResponse | null = null;
    try {
      for await (const event of chatApi.stream(threadId, text, controller.signal)) {
        if (event.event === "done") {
          final = event.data;
        } else if (event.event === "error") {
          setError(event.data.detail);
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) handleFailure(err);
    } finally {
      abortRef.current = null;
      setPending(false);
    }
    if (final) {
      setPendingAction(final.pending_action);
      appendAssistant(final);
      void queryClient.invalidateQueries({ queryKey: chatKeys.messages(threadId) });
    }
  }

  function handleNewConversation() {
    adoptThread(newThreadId());
    setMessages([]);
    setPendingAction(null);
    setError(null);
  }

  function handleResizeStart(event: ReactPointerEvent<HTMLDivElement>) {
    event.currentTarget.setPointerCapture(event.pointerId);
    resizeRef.current = {
      x: event.clientX,
      y: event.clientY,
      width: size.width,
      height: size.height,
    };
  }

  function handleResizeMove(event: ReactPointerEvent<HTMLDivElement>) {
    const start = resizeRef.current;
    if (!start) return;
    setSize(
      clampSize(
        {
          width: start.width + event.clientX - start.x,
          height: start.height + event.clientY - start.y,
        },
        { width: window.innerWidth, height: window.innerHeight },
      ),
    );
  }

  function handleResizeEnd() {
    resizeRef.current = null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-40">
      {open && (
        <div
          style={{ width: size.width, height: size.height }}
          className="relative mb-3 flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl"
        >
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
            {!ready || history.isLoading ? (
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
                          {String((call as { name?: string }).name ?? "consulta")}
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
                Cargando…
              </div>
            )}
          </div>

          {error && (
            <p className="border-t border-red-100 bg-red-50 px-3 py-2 text-xs text-red-600">
              {error}
            </p>
          )}

          {pendingAction && (
            <div className="border-t border-amber-100 bg-amber-50 px-3 py-3">
              <p className="text-xs font-semibold text-amber-800">Acción pendiente de confirmación</p>
              <p className="mt-1 text-xs text-amber-700">{pendingAction.summary}</p>
              <div className="mt-2 flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  isLoading={pending}
                  onClick={() => void handleConfirm()}
                >
                  Confirmar
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={pending}
                  onClick={handleCancelAction}
                >
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          <div className="flex items-end gap-2 border-t border-slate-100 px-4 py-4">
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

          <div
            role="separator"
            aria-label="Redimensionar asistente"
            title="Arrastrá para redimensionar"
            onPointerDown={handleResizeStart}
            onPointerMove={handleResizeMove}
            onPointerUp={handleResizeEnd}
            onLostPointerCapture={handleResizeEnd}
            className="absolute right-0 bottom-0 h-4 w-4 cursor-nwse-resize touch-none rounded-br-2xl bg-slate-100 [background-image:linear-gradient(135deg,transparent_45%,#94a3b8_45%,#94a3b8_55%,transparent_55%)] hover:bg-brand-50"
          />
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