import { describe, expect, it } from "vitest";

import { DEFAULT_SIZE, MIN_HEIGHT, MIN_WIDTH, clampSize, parseSize } from "./size";

const VIEWPORT = { width: 1440, height: 900 };

describe("clampSize", () => {
  it("respeta el tamaño por defecto", () => {
    expect(clampSize(DEFAULT_SIZE, VIEWPORT)).toEqual(DEFAULT_SIZE);
  });

  it("no deja el panel más chico que el mínimo", () => {
    const size = clampSize({ width: 100, height: 50 }, VIEWPORT);
    expect(size.width).toBe(MIN_WIDTH);
    expect(size.height).toBe(MIN_HEIGHT);
  });

  it("no deja el panel más grande que la pantalla", () => {
    const size = clampSize({ width: 5000, height: 5000 }, { width: 800, height: 600 });
    expect(size.width).toBe(800 - 32);
    expect(size.height).toBe(600 - 32);
  });
});

describe("parseSize", () => {
  it("usa el tamaño guardado si es válido", () => {
    const raw = JSON.stringify({ width: 520, height: 700 });
    expect(parseSize(raw, VIEWPORT)).toEqual({ width: 520, height: 700 });
  });

  it("usa el tamaño por defecto si no hay nada guardado", () => {
    expect(parseSize(null, VIEWPORT)).toEqual(DEFAULT_SIZE);
  });

  it("usa el tamaño por defecto si el guardado está roto", () => {
    expect(parseSize("no-es-json", VIEWPORT)).toEqual(DEFAULT_SIZE);
    expect(parseSize(JSON.stringify({ width: "grande" }), VIEWPORT)).toEqual(DEFAULT_SIZE);
  });

  it("recorta el tamaño guardado contra la pantalla actual", () => {
    const raw = JSON.stringify({ width: 4000, height: 4000 });
    expect(parseSize(raw, { width: 700, height: 500 })).toEqual({ width: 668, height: 468 });
  });
});
