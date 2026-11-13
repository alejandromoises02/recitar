import { describe, expect, it } from "vitest";
import { monthGrid, monthTitle, shiftMonth } from "./month-grid";

const TODAY = "2026-11-13";

describe("monthGrid", () => {
  const weeks = monthGrid("2026-11", TODAY);

  it("is whole weeks from Monday to Sunday covering the month", () => {
    expect(weeks).toHaveLength(6);
    expect(weeks.every((week) => week.length === 7)).toBe(true);
    expect(weeks[0][0].iso).toBe("2026-10-26");
    expect(weeks[0][6].iso).toBe("2026-11-01");
    expect(weeks[5][0].iso).toBe("2026-11-30");
  });

  it("marks the days outside the month", () => {
    expect(weeks[0][0].inMonth).toBe(false);
    expect(weeks[0][6].inMonth).toBe(true);
  });

  it("disables days before today and keeps today and later pickable", () => {
    const cells = weeks.flat();
    expect(cells.find((c) => c.iso === "2026-11-12")?.disabled).toBe(true);
    expect(cells.find((c) => c.iso === "2026-11-13")?.disabled).toBe(false);
    expect(cells.find((c) => c.iso === "2026-11-13")?.today).toBe(true);
    expect(cells.find((c) => c.iso === "2026-11-30")?.disabled).toBe(false);
  });

  it("needs only four weeks for a 28-day month that starts on a Monday", () => {
    expect(monthGrid("2027-02", TODAY)).toHaveLength(4);
  });
});

describe("shiftMonth and monthTitle", () => {
  it("moves across years", () => {
    expect(shiftMonth("2026-12", 1)).toBe("2027-01");
    expect(shiftMonth("2027-01", -1)).toBe("2026-12");
  });

  it("names the month in Spanish", () => {
    expect(monthTitle("2026-11")).toBe("Noviembre 2026");
  });
});
