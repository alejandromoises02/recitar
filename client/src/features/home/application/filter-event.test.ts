import { describe, expect, it } from "vitest";
import { filterUsed, noResults, type FilterState } from "./filter-event";

const NONE: FilterState = { text: "", venue: null, when: "all", day: null, group: "day" };

describe("filterUsed", () => {
  it("is the venue picked", () => {
    expect(filterUsed(NONE, { ...NONE, venue: "Niceto Club" })).toEqual({ filter: "venue", value: "Niceto Club" });
  });

  it("is the quick date range picked", () => {
    expect(filterUsed(NONE, { ...NONE, when: "weekend" })).toEqual({ filter: "when", value: "weekend" });
  });

  it("is the day picked, by its date, from any date or from another day", () => {
    const picked = { ...NONE, when: "day" as const, day: "2026-12-05" };
    expect(filterUsed(NONE, picked)).toEqual({ filter: "day", value: "2026-12-05" });
    expect(filterUsed(picked, { ...picked, day: "2026-12-06" })).toEqual({ filter: "day", value: "2026-12-06" });
  });

  it("is the grouping chosen", () => {
    expect(filterUsed(NONE, { ...NONE, group: "month" })).toEqual({ filter: "group", value: "month" });
  });

  it("is the search once it starts, without what was typed", () => {
    expect(filterUsed(NONE, { ...NONE, text: "n" })).toEqual({ filter: "search" });
  });

  it("is nothing while the search keeps being typed", () => {
    expect(filterUsed({ ...NONE, text: "n" }, { ...NONE, text: "ni" })).toBeNull();
  });

  it("is nothing when a filter is cleared, or when nothing changed", () => {
    expect(filterUsed({ ...NONE, venue: "Niceto Club" }, NONE)).toBeNull();
    expect(filterUsed({ ...NONE, when: "week" }, NONE)).toBeNull();
    expect(filterUsed({ ...NONE, text: "ni" }, NONE)).toBeNull();
    expect(filterUsed(NONE, NONE)).toBeNull();
  });
});

describe("noResults", () => {
  it("is nothing while no filter is on: an empty listing then says nothing about what people look for", () => {
    expect(noResults(NONE)).toBeNull();
    expect(noResults({ ...NONE, group: "month" })).toBeNull();
    expect(noResults({ ...NONE, text: "   " })).toBeNull();
  });

  it("names the filters that were on, the venue and the date asked for", () => {
    expect(noResults({ ...NONE, venue: "Niceto Club", when: "weekend" })).toEqual({ filters: ["venue", "when"], venue: "Niceto Club", when: "weekend" });
  });

  it("gives a picked day by its date", () => {
    expect(noResults({ ...NONE, when: "day", day: "2026-12-05" })).toEqual({ filters: ["day"], when: "2026-12-05" });
  });

  it("says the search was on but never what was typed", () => {
    const use = noResults({ ...NONE, text: "my name is Ana" });
    expect(use).toEqual({ filters: ["search"] });
    expect(JSON.stringify(use)).not.toContain("Ana");
  });
});
