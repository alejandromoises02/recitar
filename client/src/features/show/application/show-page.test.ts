import { describe, expect, it } from "vitest";
import type { ShowDateTickets } from "../../events/domain/show";
import { buttonWhen, dateTile, dateTargets, updatedAgo } from "./show-page";

// Saturday 14 November 2026, noon in Buenos Aires.
const NOW = new Date("2026-11-14T15:00:00Z");
const at = (iso: string) => new Date(iso);

describe("dateTile", () => {
  it("is weekday, day, short month and time in Buenos Aires", () => {
    expect(dateTile(at("2026-11-19T00:00:00Z"), NOW, "es")).toEqual({ weekday: "MIÉ", day: "18", month: "NOV", time: "21:00" });
    expect(dateTile(at("2026-11-19T00:00:00Z"), NOW, "en")).toEqual({ weekday: "WED", day: "18", month: "NOV", time: "21:00" });
  });

  it("adds a two-digit year to the month when not this year", () => {
    expect(dateTile(at("2027-02-07T00:00:00Z"), NOW, "es").month).toBe("FEB 27");
  });
});

describe("buttonWhen", () => {
  it("is the short date and time under the ticket button", () => {
    expect(buttonWhen(at("2026-11-19T00:00:00Z"), NOW, "es")).toBe("Mié 18/11 · 21:00");
    expect(buttonWhen(at("2026-11-19T00:00:00Z"), NOW, "en")).toBe("Wed 18/11 · 21:00");
    expect(buttonWhen(at("2027-02-07T00:00:00Z"), NOW, "es")).toBe("Sáb 06/02/27 · 21:00");
  });
});

describe("dateTargets", () => {
  const date = (links: { vendor: string; url: string }[]): ShowDateTickets => ({ id: "x-1", startsAt: NOW, ticketLinks: links });

  it("is one target per vendor with its domain", () => {
    expect(
      dateTargets(date([
        { vendor: "Movistar Arena", url: "https://www.movistararena.com.ar/show/1" },
        { vendor: "Ticketek", url: "https://ticketek.com.ar/x" },
      ]), "https://www.movistararena.com.ar/show/1"),
    ).toEqual([
      { vendor: "Movistar Arena", url: "https://www.movistararena.com.ar/show/1", domain: "movistararena.com.ar" },
      { vendor: "Ticketek", url: "https://ticketek.com.ar/x", domain: "ticketek.com.ar" },
    ]);
  });

  it("falls back to the source page when a date has no ticket link", () => {
    expect(dateTargets(date([]), "https://teatrocolon.org.ar/produccion/x/")).toEqual([
      { vendor: null, url: "https://teatrocolon.org.ar/produccion/x/", domain: "teatrocolon.org.ar" },
    ]);
  });
});

describe("updatedAgo", () => {
  it("says how long ago the data was read, in minutes, hours or days", () => {
    expect(updatedAgo(at("2026-11-14T14:58:00Z"), NOW, "es")).toBe("actualizado recién");
    expect(updatedAgo(at("2026-11-14T14:20:00Z"), NOW, "es")).toBe("actualizado hace 40 min");
    expect(updatedAgo(at("2026-11-13T18:00:00Z"), NOW, "es")).toBe("actualizado hace 21 h");
    expect(updatedAgo(at("2026-11-09T04:45:00Z"), NOW, "es")).toBe("actualizado hace 5 días");
    expect(updatedAgo(at("2026-11-13T14:00:00Z"), NOW, "es")).toBe("actualizado hace 1 día");
    expect(updatedAgo(at("2026-11-13T18:00:00Z"), NOW, "en")).toBe("updated 21 h ago");
    expect(updatedAgo(at("2026-11-13T14:00:00Z"), NOW, "en")).toBe("updated 1 day ago");
  });
});
