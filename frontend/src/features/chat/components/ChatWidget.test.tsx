import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ChatResponse, PendingAction } from "@/types/domain";

const apiMock = vi.hoisted(() => ({
  stream: vi.fn(),
  confirm: vi.fn(),
  threads: vi.fn(async (): Promise<unknown[]> => []),
  messages: vi.fn(async (): Promise<unknown[]> => []),
}));

const historyMock = vi.hoisted(() => ({
  value: { data: [] as unknown[], isLoading: false },
}));

vi.mock("@/features/chat/api", () => ({ chatApi: apiMock }));

vi.mock("@/features/chat/hooks", () => ({
  chatKeys: {
    threads: ["chat", "threads"],
    messages: (threadId: string) => ["chat", "messages", threadId],
  },
  useChatMessages: () => historyMock.value,
}));

import { ChatWidget } from "./ChatWidget";

const PENDING: PendingAction = {
  token: "tok-1",
  tool: "crear_cliente",
  args: { nombre: "Marta" },
  summary: "Se crea un nuevo cliente Marta.",
};

const DONE_WITH_ACTION: ChatResponse = {
  thread_id: "web-test",
  tool_calls: [{ name: "proponer_accion" }],
  response: "Propuesta registrada: Se crea un nuevo cliente Marta.",
  pending_action: PENDING,
};

function renderWidget() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ChatWidget />
    </QueryClientProvider>,
  );
}

async function openAndSend(text: string) {
  renderWidget();
  fireEvent.click(screen.getByLabelText("Abrir asistente"));
  await screen.findByText("Preguntame por tus ventas, stock o clientes.");
  fireEvent.change(screen.getByPlaceholderText("Escribí tu consulta..."), {
    target: { value: text },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar" }));
}

function streamOf(...events: { event: string; data: unknown }[]) {
  return async function* () {
    for (const event of events) yield event;
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  if (!globalThis.crypto?.randomUUID) {
    vi.stubGlobal("crypto", { randomUUID: () => "test-thread" });
  }
});

describe("ChatWidget: confirmación de acciones", () => {
  it("muestra el botón Confirmar cuando el stream trae pending_action", async () => {
    apiMock.stream.mockImplementation(
      streamOf(
        { event: "token", data: { delta: "Propuesta registrada." } },
        { event: "done", data: DONE_WITH_ACTION },
      ),
    );

    await openAndSend("creá una venta para marta");

    await screen.findByText("Acción pendiente de confirmación");
    expect(screen.getByText("Se crea un nuevo cliente Marta.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeInTheDocument();
  });

  it("al confirmar llama a la API con el token y muestra la respuesta", async () => {
    apiMock.stream.mockImplementation(
      streamOf({ event: "done", data: DONE_WITH_ACTION }),
    );
    apiMock.confirm.mockResolvedValue({
      thread_id: "web-test",
      tool_calls: [],
      response: "Cliente Marta creado.",
      pending_action: null,
    } satisfies ChatResponse);

    await openAndSend("creá una venta para marta");

    const confirmButton = await screen.findByRole("button", { name: "Confirmar" });
    fireEvent.click(confirmButton);

    await screen.findByText("Cliente Marta creado.");
    expect(apiMock.confirm).toHaveBeenCalledWith(expect.any(String), "tok-1");
    await waitFor(() =>
      expect(screen.queryByText("Acción pendiente de confirmación")).not.toBeInTheDocument(),
    );
  });

  it("al cancelar descarta la propuesta sin llamar a la API", async () => {
    apiMock.stream.mockImplementation(
      streamOf({ event: "done", data: DONE_WITH_ACTION }),
    );

    await openAndSend("creá una venta para marta");

    const cancelButton = await screen.findByRole("button", { name: "Cancelar" });
    fireEvent.click(cancelButton);

    await screen.findByText("Acción cancelada. No se modificó nada.");
    expect(apiMock.confirm).not.toHaveBeenCalled();
    expect(screen.queryByText("Acción pendiente de confirmación")).not.toBeInTheDocument();
  });

  it("una consulta sin propuesta no muestra botón de confirmación", async () => {
    apiMock.stream.mockImplementation(
      streamOf({
        event: "done",
        data: {
          thread_id: "web-test",
          tool_calls: [{ name: "consultar_saldo_cliente" }],
          response: "Camila debe 53.200 en 1 orden.",
          pending_action: null,
        } satisfies ChatResponse,
      }),
    );

    await openAndSend("cuánto debe camila duarte");

    await screen.findByText("Camila debe 53.200 en 1 orden.");
    expect(screen.queryByRole("button", { name: "Confirmar" })).not.toBeInTheDocument();
  });

  it("mientras espera muestra Cargando y no el texto crudo del stream", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    apiMock.stream.mockImplementation(async function* () {
      yield { event: "token", data: { delta: '{"name": "reponer_stock", "arguments": {}}' } };
      await gate;
      yield {
        event: "done",
        data: {
          thread_id: "web-test",
          tool_calls: [{ name: "listar_productos_a_reponer" }],
          response: "No hay productos para reponer.",
          pending_action: null,
        } satisfies ChatResponse,
      };
    });

    await openAndSend("de qué productos debo reponer stock");

    expect(await screen.findByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByText(/"name"/)).not.toBeInTheDocument();

    release();
    await screen.findByText("No hay productos para reponer.");
    expect(screen.queryByText("Cargando…")).not.toBeInTheDocument();
  });
});
