import { beforeEach, describe, expect, it, vi } from "vitest";

import { usersApi, workApi } from "./api";

const { get, post, patch } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  patch: vi.fn(),
}));

vi.mock("@/lib/http", () => ({ api: { get, post, patch } }));

describe("workApi", () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
    patch.mockReset();
  });

  it("lista el tablero con los filtros activos y omite los vac�os", async () => {
    get.mockResolvedValue({ data: [] });
    await workApi.list({ priority: "alta", assigned_to: "" });
    expect(get).toHaveBeenCalledWith("/work-items?priority=alta");
  });

  it("actualiza el estado de trabajo de una tarjeta", async () => {
    patch.mockResolvedValue({ data: { sale_id: "1" } });
    const result = await workApi.update("1", { status: "en_curso" });
    expect(patch).toHaveBeenCalledWith("/work-items/1", { status: "en_curso" });
    expect(result).toEqual({ sale_id: "1" });
  });

  it("agrega un comentario", async () => {
    post.mockResolvedValue({ data: { sale_id: "1" } });
    await workApi.addComment("1", "Revisar");
    expect(post).toHaveBeenCalledWith("/work-items/1/comments", { text: "Revisar" });
  });
});

describe("usersApi", () => {
  beforeEach(() => get.mockReset());

  it("lista los usuarios activos", async () => {
    get.mockResolvedValue({ data: [{ id: "u1", name: "A", email: null }] });
    const users = await usersApi.list();
    expect(get).toHaveBeenCalledWith("/users");
    expect(users[0].id).toBe("u1");
  });
});
