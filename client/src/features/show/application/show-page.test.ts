import { describe, expect, it } from "vitest";
import type { Show, ShowDateTickets } from "../../events/domain/show";
import { buttonWhen, dateMode, dateTile, dateTargets, hasVenueToExplore, mapEmbedUrl, moreAtVenue, ticketPlan, updatedAgo, venueMapQuery } from "./show-page";

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

  it("says the time is to be confirmed when it is unknown", () => {
    expect(dateTile(at("2026-11-18T03:00:00Z"), NOW, "es", false).time).toBe("A confirmar");
  });
});

describe("buttonWhen", () => {
  it("is the short date and time under the ticket button", () => {
    expect(buttonWhen(at("2026-11-19T00:00:00Z"), NOW, "es")).toBe("Mié 18/11 · 21:00");
    expect(buttonWhen(at("2026-11-19T00:00:00Z"), NOW, "en")).toBe("Wed 18/11 · 21:00");
    expect(buttonWhen(at("2027-02-07T00:00:00Z"), NOW, "es")).toBe("Sáb 06/02/27 · 21:00");
  });

  it("says the time is to be confirmed when it is unknown", () => {
    expect(buttonWhen(at("2026-11-18T03:00:00Z"), NOW, "es", false)).toBe("Mié 18/11 · Hora a confirmar");
  });
});

describe("dateTargets", () => {
  const date = (links: { vendor: string; url: string }[]): ShowDateTickets => ({ id: "x-1", startsAt: NOW, timeKnown: true, ticketLinks: links });

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

describe("dateMode and ticketPlan", () => {
  const SOURCE = "https://teatrocolon.org.ar/produccion/x/";
  const date = (id: string, urls: string[]): ShowDateTickets => ({
    id,
    startsAt: NOW,
    timeKnown: true,
    ticketLinks: urls.map((url) => ({ vendor: "Entradas BA", url })),
  });
  const SHARED = "https://entradasba.buenosaires.gob.ar/evento/1";

  it("lists the dates when they all share one ticket page: the date is picked on the ticketer's site", () => {
    const dates = [date("a", [SHARED]), date("b", [SHARED]), date("c", [])];
    expect(dateMode(dates)).toBe("list");
    expect(ticketPlan(dates, 0, SOURCE)).toEqual({ kind: "any-date", eventId: "a", targets: [{ vendor: "Entradas BA", url: SHARED, domain: "entradasba.buenosaires.gob.ar" }] });
  });

  it("lets you pick when dates have their own ticket pages, and the plan follows the picked date", () => {
    const dates = [date("a", ["https://t.example/a"]), date("b", ["https://t.example/b"])];
    expect(dateMode(dates)).toBe("pick");
    expect(ticketPlan(dates, 1, SOURCE)).toEqual({ kind: "date", eventId: "b", targets: [{ vendor: "Entradas BA", url: "https://t.example/b", domain: "t.example" }] });
  });

  it("is a single date when there is one", () => {
    expect(dateMode([date("a", [SHARED])])).toBe("single");
    expect(ticketPlan([date("a", [SHARED])], 0, SOURCE).kind).toBe("date");
  });

  it("says a date is not on sale yet and points to the official page", () => {
    expect(ticketPlan([date("a", [])], 0, SOURCE)).toEqual({ kind: "not-on-sale", eventId: "a", source: { url: SOURCE, domain: "teatrocolon.org.ar" } });
    const picked = [date("a", ["https://t.example/a"]), date("b", ["https://t.example/b"]), date("c", [])];
    expect(dateMode(picked)).toBe("pick");
    expect(ticketPlan(picked, 2, SOURCE).kind).toBe("not-on-sale");
  });

  it("is not on sale when no listed date has a link yet", () => {
    expect(dateMode([date("a", []), date("b", [])])).toBe("list");
    expect(ticketPlan([date("a", []), date("b", [])], 0, SOURCE).kind).toBe("not-on-sale");
  });

  it("names the date the click is counted for: the picked one, the first one on sale, else the first", () => {
    const picked = [date("a", ["https://t.example/a"]), date("b", ["https://t.example/b"]), date("c", [])];
    expect(ticketPlan(picked, 1, SOURCE)).toMatchObject({ eventId: "b" });
    expect(ticketPlan(picked, 2, SOURCE)).toMatchObject({ eventId: "c" });
    expect(ticketPlan([date("a", []), date("b", [SHARED]), date("c", [SHARED])], 0, SOURCE)).toMatchObject({ eventId: "b" });
    expect(ticketPlan([date("a", []), date("b", [])], 1, SOURCE)).toMatchObject({ eventId: "a" });
  });
});

describe("moreAtVenue", () => {
  const shows = (...ids: string[]) => ids.map((id) => ({ id }) as Show);

  it("is up to 4 other shows at the venue, in the order they came", () => {
    expect(moreAtVenue(shows("a", "b", "c", "d", "e"), "x").map((s) => s.id)).toEqual(["a", "b", "c", "d"]);
  });

  it("never includes the current show", () => {
    expect(moreAtVenue(shows("a", "x", "b", "c", "d"), "x").map((s) => s.id)).toEqual(["a", "b", "c", "d"]);
  });

  it("is empty when the current show is the only one there", () => {
    expect(moreAtVenue(shows("x"), "x")).toEqual([]);
  });
});

describe("hasVenueToExplore", () => {
  it("is a real venue", () => {
    expect(hasVenueToExplore("Niceto Club")).toBe(true);
  });

  it("is not a venue still to be confirmed, whose other shows have nothing in common", () => {
    expect(hasVenueToExplore("Lugar a confirmar")).toBe(false);
  });
});

describe("venueMapQuery", () => {
  const where = (venue: string, city: string | null, address: string | null | undefined) => ({
    venue,
    city,
    venueLocation: address === undefined ? null : { address, latitude: -34.59, longitude: -58.44 },
  });

  it("is the venue, its street address and its city", () => {
    expect(venueMapQuery(where("Movistar Arena", "Buenos Aires", "Humboldt 450"))).toBe("Movistar Arena, Humboldt 450, Buenos Aires");
  });

  it("leaves out what is unknown, so a venue without coordinates is still searched by name", () => {
    expect(venueMapQuery(where("Movistar Arena", "Buenos Aires", null))).toBe("Movistar Arena, Buenos Aires");
    expect(venueMapQuery(where("XLR Club", "Buenos Aires", undefined))).toBe("XLR Club, Buenos Aires");
    expect(venueMapQuery(where("XLR Club", null, undefined))).toBe("XLR Club");
  });

  it("is null while the venue is to be confirmed", () => {
    expect(venueMapQuery(where("Lugar a confirmar", "Buenos Aires", undefined))).toBeNull();
  });
});

describe("mapEmbedUrl", () => {
  it("is Google's embeddable map for the query, in the app language", () => {
    expect(mapEmbedUrl("Movistar Arena, Humboldt 450, Buenos Aires", "es")).toBe(
      "https://maps.google.com/maps?q=Movistar%20Arena%2C%20Humboldt%20450%2C%20Buenos%20Aires&z=16&hl=es&output=embed",
    );
    expect(mapEmbedUrl("Niceto Club", "en")).toBe("https://maps.google.com/maps?q=Niceto%20Club&z=16&hl=en&output=embed");
  });
});
