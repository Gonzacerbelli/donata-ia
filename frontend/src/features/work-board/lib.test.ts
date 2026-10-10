import { describe, expect, it } from "vitest";

import type { WorkCard } from "@/types/domain";

import { WORK_PRIORITIES, WORK_STATUSES, groupByStatus, summarizeItems } from "./lib";

function card(overrides: Partial<WorkCard>): WorkCard {
  return {
    sale_id: "s1",
    client_id: "c1",
    date: "2024-05-01T00:00:00Z",
    items: [{ product_id: null, description: "Alfombra", qty: 1, unit_price: 100 }],
    total: 100,
    status: "pendiente",
    priority: "media",
    assigned_to: null,
    comments: [],
    ...overrides,
  };
}

describe("groupByStatus", () => {
  it("agrupa las tarjetas en las cuatro columnas", () => {
    const grouped = groupByStatus([
      card({ sale_id: "s1", status: "pendiente" }),
      card({ sale_id: "s2", status: "en_curso" }),
      card({ sale_id: "s3", status: "terminado" }),
    ]);
    expect(WORK_STATUSES).toEqual(["pendiente", "en_curso", "bloqueado", "terminado"]);
    expect(grouped.pendiente.map((item) => item.sale_id)).toEqual(["s1"]);
    expect(grouped.en_curso.map((item) => item.sale_id)).toEqual(["s2"]);
    expect(grouped.bloqueado).toEqual([]);
    expect(grouped.terminado.map((item) => item.sale_id)).toEqual(["s3"]);
  });
});

describe("summarizeItems", () => {
  it("resume las descripciones de la orden", () => {
    expect(
      summarizeItems([
        { product_id: null, description: "Alfombra", qty: 1, unit_price: 100 },
        { product_id: null, description: "Servicio", qty: 1, unit_price: 50 },
      ]),
    ).toBe("Alfombra, Servicio");
  });

  it("usa un texto por defecto sin �tems", () => {
    expect(summarizeItems([])).toBe("Sin �tems");
  });

  it("expone las tres prioridades", () => {
    expect(WORK_PRIORITIES).toEqual(["alta", "media", "baja"]);
  });
});
