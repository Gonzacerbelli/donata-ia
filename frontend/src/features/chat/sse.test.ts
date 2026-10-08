import { describe, expect, it } from "vitest";

import { createSseParser } from "./sse";

describe("createSseParser", () => {
  it("parsea un frame completo", () => {
    const parse = createSseParser();
    const events = parse('event: token\ndata: {"delta": "Hola"}\n\n');
    expect(events).toEqual([{ event: "token", data: { delta: "Hola" } }]);
  });

  it("maneja un frame partido entre dos lecturas", () => {
    const parse = createSseParser();
    expect(parse('event: token\ndata: {"del')).toEqual([]);
    const events = parse('ta": "Hola"}\n\n');
    expect(events).toEqual([{ event: "token", data: { delta: "Hola" } }]);
  });

  it("parsea frames múltiples en un mismo chunk", () => {
    const parse = createSseParser();
    const events = parse(
      'event: start\ndata: {"thread_id": "t1"}\n\nevent: token\ndata: {"delta": "Hola"}\n\n',
    );
    expect(events).toEqual([
      { event: "start", data: { thread_id: "t1" } },
      { event: "token", data: { delta: "Hola" } },
    ]);
  });

  it("conserva el buffer incompleto hasta el siguiente chunk", () => {
    const parse = createSseParser();
    expect(parse("event: done\ndata: {")).toEqual([]);
    expect(parse('"response": "ok"}\n\nevent: token\ndata: {"del')).toEqual([
      { event: "done", data: { response: "ok" } },
    ]);
    expect(parse('ta": "x"}\n\n')).toEqual([{ event: "token", data: { delta: "x" } }]);
  });

  it("devuelve data null cuando el payload no es JSON válido", () => {
    const parse = createSseParser();
    expect(parse("event: error\ndata: no-es-json\n\n")).toEqual([
      { event: "error", data: null },
    ]);
  });

  it("ignora frames sin nombre de evento", () => {
    const parse = createSseParser();
    expect(parse("data: {}\n\n")).toEqual([]);
  });
});
