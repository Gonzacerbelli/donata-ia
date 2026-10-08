import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Sale } from "@/types/domain";

import { ClientSummary } from "./ClientSummary";

const useClientSalesMock = vi.hoisted(() => vi.fn());

vi.mock("../hooks", () => ({ useClientSales: useClientSalesMock }));

function sale(overrides: Partial<Sale>): Sale {
  return {
    id: "s1",
    client_id: "c1",
    client_type: "minorista",
    date: "2026-01-15",
    items: [],
    subtotal: 1000,
    shipping_cost: 0,
    discount: 0,
    discount_pct: null,
    total: 1000,
    status: "entregado",
    payments: [],
    notes: null,
    ship_by: null,
    payment_due: null,
    created_at: "2026-01-15",
    updated_at: "2026-01-15",
    paid: 400,
    balance: 600,
    ...overrides,
  };
}

const client = { id: "c1", name: "Camila Duarte" } as Parameters<
  typeof ClientSummary
>[0]["client"];

describe("ClientSummary", () => {
  it("excluye las canceladas del saldo pendiente", () => {
    useClientSalesMock.mockReturnValue({
      data: [sale({ id: "a1", balance: 600 }), sale({ id: "a2", status: "cancelado", balance: 1000 })],
      isLoading: false,
      error: null,
    });

    render(<ClientSummary client={client} />);

    expect(screen.getByText("Saldo pendiente")).toBeInTheDocument();
    expect(screen.getByText("$600")).toBeInTheDocument();
    expect(screen.queryByText("$1.600")).not.toBeInTheDocument();
  });

  it("muestra la orden cancelada como Cancelada y sin deuda", () => {
    useClientSalesMock.mockReturnValue({
      data: [
        sale({ id: "a1", paid: 1000, balance: 0 }),
        sale({ id: "a2", status: "cancelado", balance: 1000 }),
      ],
      isLoading: false,
      error: null,
    });

    render(<ClientSummary client={client} />);

    expect(screen.getByText("Cancelada")).toBeInTheDocument();
    expect(screen.queryByText("Debe $1.000")).not.toBeInTheDocument();
    expect(screen.getByText("$0")).toBeInTheDocument();
  });
});
