import { describe, expect, it } from "vitest";
import type { Event, EventCategory } from "../domain/event";
import { VISIBLE_CATEGORIES, filterVisible } from "./visible-events";

const make = (id: string, category: EventCategory): Event => ({
  id,
  category,
  title: id,
  artist: null,
  venue: "Niceto Club",
  city: "Buenos Aires",
  region: "AR-C",
  country: "AR",
  startsAt: new Date("2026-11-20T21:00:00Z"),
  ticketLinks: [],
  sourceUrl: "https://example.com",
  imageUrl: null,
  imageOrigin: null,
  imageAuthor: null,
  imageLicense: null,
  imageSourceUrl: null,
  updatedAt: new Date("2026-11-08T00:00:00Z"),
});

describe("filterVisible", () => {
  const events = [
    make("a", "concert"),
    make("b", "party"),
    make("c", "theatre"),
    make("d", "other"),
  ];

  it("shows only concerts for now", () => {
    expect(VISIBLE_CATEGORIES).toEqual(["concert"]);
    expect(filterVisible(events).map((e) => e.id)).toEqual(["a"]);
  });

  it("accepts other categories so they can be enabled later", () => {
    expect(filterVisible(events, ["concert", "party"]).map((e) => e.id)).toEqual(["a", "b"]);
  });
});
