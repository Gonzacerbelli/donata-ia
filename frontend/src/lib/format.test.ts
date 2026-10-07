import { describe, expect, it } from "vitest";

import { formatCurrency, formatDate, formatDateInput } from "./format";

describe("formatCurrency", () => {
  it("formatea importes en ARS sin decimales", () => {
    expect(formatCurrency(1234)).toBe("$1.234");
    expect(formatCurrency(1000000)).toBe("$1.000.000");
  });

  it("trata nulos como cero", () => {
    expect(formatCurrency(null)).toBe("$0");
  });
});

describe("formatDate", () => {
  it("formatea fechas ISO de sólo fecha como DD/MM/AAAA", () => {
    expect(formatDate("2025-03-09")).toBe("09/03/2025");
  });

  it("devuelve guion para valores vacíos o inválidos", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("no-es-fecha")).toBe("—");
  });
});

describe("formatDateInput", () => {
  it("devuelve el formato del input date", () => {
    expect(formatDateInput(new Date(2025, 2, 9))).toBe("2025-03-09");
  });
});