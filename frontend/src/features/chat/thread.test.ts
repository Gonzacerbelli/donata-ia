import { beforeEach, describe, expect, it, vi } from "vitest";

import { THREAD_KEY, resolveThreadId } from "./thread";

vi.mock("./api", () => ({
  chatApi: {
    threads: vi.fn(),
  },
}));

const { chatApi } = await import("./api");
const threads = vi.mocked(chatApi.threads);

const HILLO_GUARDADO = "web-guardado";
const HILLO_OTRO = "web-otro";

beforeEach(() => {
  localStorage.clear();
  threads.mockReset();
});

describe("resolveThreadId", () => {
  it("devuelve el hilo guardado cuando pertenece al usuario", async () => {
    localStorage.setItem(THREAD_KEY, HILLO_GUARDADO);
    threads.mockResolvedValue([
      { thread_id: HILLO_OTRO },
      { thread_id: HILLO_GUARDADO },
    ] as Awaited<ReturnType<typeof chatApi.threads>>);

    expect(await resolveThreadId()).toBe(HILLO_GUARDADO);
  });

  it("devuelve el hilo más reciente si el guardado no le pertenece", async () => {
    localStorage.setItem(THREAD_KEY, "web-clave-ajena");
    threads.mockResolvedValue([{ thread_id: HILLO_OTRO }] as Awaited<
      ReturnType<typeof chatApi.threads>
    >);

    expect(await resolveThreadId()).toBe(HILLO_OTRO);
  });

  it("crea un hilo nuevo si el usuario todavía no tiene conversaciones", async () => {
    threads.mockResolvedValue([] as Awaited<ReturnType<typeof chatApi.threads>>);

    const threadId = await resolveThreadId();
    expect(threadId).toMatch(/^web-/);
    expect(threads).toHaveBeenCalledTimes(1);
  });

  it("usa lo guardado cuando la API no responde", async () => {
    localStorage.setItem(THREAD_KEY, HILLO_GUARDADO);
    threads.mockRejectedValue(new Error("sin conexión"));

    expect(await resolveThreadId()).toBe(HILLO_GUARDADO);
  });

  it("genera un hilo nuevo cuando no hay nada guardado y la API no responde", async () => {
    threads.mockRejectedValue(new Error("sin conexión"));

    expect(await resolveThreadId()).toMatch(/^web-/);
  });
});
