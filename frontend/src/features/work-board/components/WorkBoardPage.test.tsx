import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { WorkBoardPage } from "./WorkBoardPage";

vi.mock("../hooks", () => {
  const sample = {
    sale_id: "s1",
    client_id: "c1",
    date: "2024-05-01T00:00:00Z",
    items: [{ product_id: null, description: "Alfombra", qty: 1, unit_price: 100 }],
    total: 100,
    status: "pendiente",
    priority: "media",
    assigned_to: null,
    comments: [],
  };
  return {
    useWorkBoard: () => ({ data: [sample], isLoading: false, error: null, refetch: vi.fn() }),
    useUpdateWork: () => ({ mutate: vi.fn(), isPending: false }),
    useAddComment: () => ({ mutate: vi.fn(), isPending: false, error: null }),
    useUsers: () => ({ data: [] }),
  };
});

describe("WorkBoardPage", () => {
  it("renderiza las columnas y la tarjeta del tablero", () => {
    render(
      <MemoryRouter initialEntries={["/trabajo"]}>
        <WorkBoardPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("heading", { name: "Trabajo" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Pendiente" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "En curso" })).toBeInTheDocument();
    expect(screen.getByText("Alfombra")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Comentarios (0)" })).toBeInTheDocument();
  });
});
