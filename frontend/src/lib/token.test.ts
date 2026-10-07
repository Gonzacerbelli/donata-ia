import { afterEach, describe, expect, it } from "vitest";

import { tokenStore } from "./token";

function makeToken(expSeconds: number): string {
  return `h.${btoa(JSON.stringify({ exp: expSeconds }))}.s`;
}

afterEach(() => {
  localStorage.clear();
});

describe("tokenStore", () => {
  it("descarta un token vencido y lo borra del storage", () => {
    tokenStore.set(makeToken(Math.floor(Date.now() / 1000) - 60));
    expect(tokenStore.get()).toBeNull();
    expect(localStorage.getItem("donata.token")).toBeNull();
  });

  it("conserva un token vigente", () => {
    const token = makeToken(Math.floor(Date.now() / 1000) + 3600);
    tokenStore.set(token);
    expect(tokenStore.get()).toBe(token);
  });

  it("descarta un token con payload ilegible", () => {
    tokenStore.set("esto.no.es.un-jwt");
    expect(tokenStore.get()).toBeNull();
  });

  it("clear elimina el token", () => {
    tokenStore.set(makeToken(Math.floor(Date.now() / 1000) + 3600));
    tokenStore.clear();
    expect(tokenStore.get()).toBeNull();
  });
});
