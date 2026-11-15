import { describe, expect, it } from "vitest";
import type { Show } from "../../events/domain/show";
import { ticketTarget } from "./ticket-target";

const show = (ticketLinks: { vendor: string; url: string }[], sourceUrl = "https://www.nicetoclub.com/show/1"): Show => ({
  id: "s",
  category: "concert",
  title: "T",
  name: "T",
  artist: null,
  venue: "V",
  city: null,
  region: null,
  country: null,
  sourceUrl,
  imageUrl: null,
  imageOrigin: null,
  imageAuthor: null,
  imageLicense: null,
  imageSourceUrl: null,
  firstSeenAt: new Date("2026-11-01T12:00:00Z"), updatedAt: new Date("2026-11-01T12:00:00Z"),
  dates: [{ id: "s-0", startsAt: new Date("2026-12-01T23:00:00Z"), timeKnown: true, ticketLinks }],
});

describe("ticketTarget", () => {
  it("is the first ticket link of the next date, with its domain", () => {
    expect(ticketTarget(show([{ vendor: "Venti", url: "https://venti.live/a/0" }, { vendor: "X", url: "https://x.com" }]))).toEqual({
      url: "https://venti.live/a/0",
      domain: "venti.live",
    });
  });

  it("falls back to the source page when the date has no ticket link", () => {
    expect(ticketTarget(show([]))).toEqual({ url: "https://www.nicetoclub.com/show/1", domain: "nicetoclub.com" });
  });

  it("drops the port and path from the domain", () => {
    expect(ticketTarget(show([{ vendor: "L", url: "http://tickets.example.com:8080/x?y=1" }])).domain).toBe("tickets.example.com");
  });
});
