import { describe, expect, it } from "vitest";
import { apiShow } from "./api-fixtures";
import type { ApiFeatured } from "./event-from-api";
import { featuredFromApi, showFromApi } from "./event-from-api";

describe("showFromApi", () => {
  it("renames every field and reads every date", () => {
    const api = apiShow("venti-mila", ["2026-11-14T22:00:00-03:00", "2026-11-21T22:00:00-03:00"]);
    api.dates[1].time_known = false;
    const show = showFromApi(api);
    expect(show).toEqual({
      id: "venti-mila",
      category: "concert",
      title: "VENTI-MILA en Niceto Bar",
      name: "Show venti-mila",
      artist: "Artista",
      venue: "Niceto Club",
      city: "Buenos Aires",
      region: "AR-C",
      country: "AR",
      sourceUrl: "https://venti.live/venti-mila",
      imageUrl: "/media/x.webp",
      imageOrigin: "licensed",
      imageAuthor: "Ana",
      imageLicense: "CC BY 4.0",
      imageSourceUrl: "https://commons.wikimedia.org/wiki/File:X.jpg",
      firstSeenAt: new Date("2026-11-02T12:00:00Z"),
      updatedAt: new Date("2026-11-13T12:00:00Z"),
      dates: [
        { id: "venti-mila-0", startsAt: new Date("2026-11-15T01:00:00Z"), timeKnown: true, ticketLinks: [{ vendor: "Venti", url: "https://venti.live/venti-mila/0" }] },
        { id: "venti-mila-1", startsAt: new Date("2026-11-22T01:00:00Z"), timeKnown: false, ticketLinks: [{ vendor: "Venti", url: "https://venti.live/venti-mila/1" }] },
      ],
    });
  });
});

describe("featuredFromApi", () => {
  it("keeps the kind and maps every show", () => {
    const api: ApiFeatured = { kind: "just_announced", items: [apiShow("a"), apiShow("b")] };
    const featured = featuredFromApi(api);
    expect(featured.kind).toBe("just_announced");
    expect(featured.items.map((s) => s.id)).toEqual(["a", "b"]);
  });
});
