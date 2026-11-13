import { describe, expect, it } from "vitest";
import type { Event } from "../domain/event";
import { pickFeatured } from "./pick-featured";

const NOW = new Date("2026-10-26T12:00:00Z");

const make = (id: string, startsAt: string, category: Event["category"] = "concert"): Event => ({
  id,
  category,
  title: `Artist ${id}`,
  artist: null,
  venue: "Niceto Club",
  city: "Buenos Aires",
  region: "AR-C",
  country: "AR",
  startsAt: new Date(startsAt),
  ticketLinks: [],
  sourceUrl: "https://example.com",
  imageUrl: null,
  imageOrigin: null,
  imageAuthor: null,
  imageLicense: null,
  imageSourceUrl: null,
  updatedAt: NOW,
  firstSeenAt: NOW,
});

describe("pickFeatured", () => {
  it("leaves out categories that are not shown yet", () => {
    const party = make("party", "2026-10-28T21:00:00Z", "party");
    const concert = make("concert", "2026-10-29T21:00:00Z");
    expect(pickFeatured([party, concert], [], NOW, 5).map((e) => e.id)).toEqual(["concert"]);
  });

  const a = make("a", "2026-10-30T21:00:00Z");
  const b = make("b", "2026-10-27T21:00:00Z");
  const c = make("c", "2026-11-02T21:00:00Z");
  const past = make("past", "2026-10-20T21:00:00Z");

  it("puts manually curated events first, in curated order", () => {
    const result = pickFeatured([a, b, c], ["c", "a"], NOW, 3);
    expect(result.map((e) => e.id)).toEqual(["c", "a", "b"]);
  });

  it("fills the rest with the soonest upcoming events", () => {
    const result = pickFeatured([a, b, c], [], NOW, 2);
    expect(result.map((e) => e.id)).toEqual(["b", "a"]);
  });

  it("never returns past events, even when curated", () => {
    const result = pickFeatured([past, a], ["past"], NOW, 5);
    expect(result.map((e) => e.id)).toEqual(["a"]);
  });

  it("ignores curated ids that do not exist and does not repeat events", () => {
    const result = pickFeatured([a, b], ["zzz", "a", "a"], NOW, 5);
    expect(result.map((e) => e.id)).toEqual(["a", "b"]);
  });

  it("respects the limit", () => {
    expect(pickFeatured([a, b, c], ["c"], NOW, 1).map((e) => e.id)).toEqual(["c"]);
  });
});
