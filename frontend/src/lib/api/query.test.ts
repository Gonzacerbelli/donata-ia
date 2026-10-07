import { describe, expect, it } from "vitest";

import { toQuery } from "./query";

describe("toQuery", () => {
  it("returns empty string when there are no usable params", () => {
    expect(toQuery({ a: undefined, b: null, c: "" })).toBe("");
  });

  it("encodes defined values", () => {
    expect(toQuery({ search: "silla", active_only: true, page: 2 })).toBe(
      "?search=silla&active_only=true&page=2",
    );
  });

  it("skips empty values but keeps real ones", () => {
    expect(toQuery({ status: "pendiente", client_id: undefined })).toBe("?status=pendiente");
  });
});