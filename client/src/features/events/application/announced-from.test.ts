import { describe, expect, it } from "vitest";
import { JUST_ANNOUNCED_DAYS, announcedFrom } from "./announced-from";

describe("announcedFrom", () => {
  it("is the Buenos Aires day 14 days before today, as YYYY-MM-DD", () => {
    expect(JUST_ANNOUNCED_DAYS).toBe(14);
    expect(announcedFrom(new Date("2026-11-13T15:00:00Z"))).toBe("2026-10-30");
  });

  it("uses the Buenos Aires day, not the UTC one, late at night", () => {
    // 01:30 UTC on the 14th is still 22:30 on the 13th in Buenos Aires.
    expect(announcedFrom(new Date("2026-11-14T01:30:00Z"))).toBe("2026-10-30");
  });

  it("crosses month and year boundaries", () => {
    expect(announcedFrom(new Date("2027-01-05T15:00:00Z"))).toBe("2026-12-22");
  });
});
