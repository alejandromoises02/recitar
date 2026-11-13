import { describe, expect, it } from "vitest";
import { FLUID_MAX_WIDTH, FLUID_MIN_WIDTH, fluid } from "./fluid";

describe("fluid", () => {
  const size = { min: 30, max: 72 };

  it("is the minimum on small screens and the maximum on large ones", () => {
    expect(fluid(size, 320)).toBe(30);
    expect(fluid(size, FLUID_MIN_WIDTH)).toBe(30);
    expect(fluid(size, FLUID_MAX_WIDTH)).toBe(72);
    expect(fluid(size, 2560)).toBe(72);
  });

  it("grows linearly in between, rounded to whole points", () => {
    const middle = (FLUID_MIN_WIDTH + FLUID_MAX_WIDTH) / 2;
    expect(fluid(size, middle)).toBe(51);
  });

  it("a fixed size stays fixed", () => {
    expect(fluid({ min: 15, max: 15 }, 1000)).toBe(15);
  });
});
