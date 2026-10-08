import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { tokenStore } from "@/lib/token";
import type { ChatStreamEvent } from "@/types/domain";

import { chatApi } from "./api";

function makeToken(): string {
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 3600 }));
  return `header.${payload}.signature`;
}

function streamResponse(chunks: string[], status = 200, headers: Record<string, string> = {}) {
  const encoder = new TextEncoder();
  let index = 0;
  const body = {
    getReader() {
      return {
        read: async () => {
          if (index >= chunks.length) return { done: true, value: undefined };
          return { done: false, value: encoder.encode(chunks[index++]) };
        },
      };
    },
  };
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (name: string) => headers[name.toLowerCase()] ?? null },
    body,
    json: async () => JSON.parse(chunks.join("") || "{}"),
  };
}

async function collect(stream: AsyncGenerator<ChatStreamEvent>): Promise<ChatStreamEvent[]> {
  const events: ChatStreamEvent[] = [];
  for await (const event of stream) events.push(event);
  return events;
}

describe("chatApi.stream", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockReset();
    tokenStore.set(makeToken());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    tokenStore.clear();
  });

  it("envía el turno con Bearer y devuelve los eventos parseados", async () => {
    fetchMock.mockResolvedValue(
      streamResponse([
        'event: start\ndata: {"thread_id": "t1"}\n\n',
        'event: token\ndata: {"delta": "Hola "}\n\n',
        'event: done\ndata: {"thread_id": "t1", "response": "Hola mundo", "tool_calls": [], "pending_action": null}\n\n',
      ]),
    );

    const events = await collect(chatApi.stream("t1", "hola"));

    expect(events.map((event) => event.event)).toEqual(["start", "token", "done"]);
    expect(events[1]).toEqual({ event: "token", data: { delta: "Hola " } });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/chat/stream");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ thread_id: "t1", message: "hola" });
    expect((init.headers as Record<string, string>).Authorization).toMatch(/^Bearer /);
  });

  it("arma frames que llegan partidos entre lecturas", async () => {
    fetchMock.mockResolvedValue(
      streamResponse(['event: token\ndata: {"del', 'ta": "Hola"}\n\n']),
    );

    const events = await collect(chatApi.stream("t1", "hola"));

    expect(events).toEqual([{ event: "token", data: { delta: "Hola" } }]);
  });

  it("propaga AbortError cuando la señal se aborta", async () => {
    const controller = new AbortController();
    fetchMock.mockImplementation(
      (_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
          controller.abort();
        }),
    );

    await expect(collect(chatApi.stream("t1", "hola", controller.signal))).rejects.toMatchObject({
      name: "AbortError",
    });
  });

  it("lanza ApiError con Retry-After cuando el rate limit responde 429", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      headers: { get: (name: string) => (name === "Retry-After" ? "42" : null) },
      json: async () => ({ detail: "Demasiadas solicitudes." }),
      body: null,
    });

    await expect(collect(chatApi.stream("t1", "hola"))).rejects.toMatchObject({
      name: "ApiError",
      status: 429,
      retryAfter: 42,
      message: "Demasiadas solicitudes.",
    });
  });

  it("lanza ApiError con el detail del backend en errores 401", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      headers: { get: () => null },
      json: async () => ({ detail: "Token inválido o expirado" }),
      body: null,
    });

    await expect(collect(chatApi.stream("t1", "hola"))).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Token inválido o expirado",
    });
  });
});
