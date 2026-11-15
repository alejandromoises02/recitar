import { describe, expect, it } from "vitest";
import type { Show } from "../../events/domain/show";
import { ticketTarget, trackedTicketUrl } from "./ticket-target";

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
      eventId: "s-0",
      vendor: "Venti",
    });
  });

  it("falls back to the source page when the date has no ticket link", () => {
    expect(ticketTarget(show([]))).toEqual({ url: "https://www.nicetoclub.com/show/1", domain: "nicetoclub.com", eventId: "s-0", vendor: null });
  });

  it("drops the port and path from the domain", () => {
    expect(ticketTarget(show([{ vendor: "L", url: "http://tickets.example.com:8080/x?y=1" }])).domain).toBe("tickets.example.com");
  });
});

describe("trackedTicketUrl", () => {
  const API = "https://api.example";

  it("is the API's /go address for the date, with the ticketer and where the click came from", () => {
    expect(trackedTicketUrl(API, "venti-mila-20261120T2100", "Venti", "show")).toBe("https://api.example/go/venti-mila-20261120T2100?v=Venti&from=show");
  });

  it("leaves the ticketer out when the date has no link and the click goes to the source page", () => {
    expect(trackedTicketUrl(API, "venti-mila-20261120T2100", null, "spotlight")).toBe("https://api.example/go/venti-mila-20261120T2100?from=spotlight");
  });

  it("encodes what is not safe in an address", () => {
    expect(trackedTicketUrl(API, "a b/c", "Entradas BA & Co", "show")).toBe("https://api.example/go/a%20b%2Fc?v=Entradas%20BA%20%26%20Co&from=show");
  });

  it("does not double the slash when the API address ends with one", () => {
    expect(trackedTicketUrl("http://192.168.0.109:8000/", "x-1", null, "show")).toBe("http://192.168.0.109:8000/go/x-1?from=show");
  });
});
