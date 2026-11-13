import { describe, expect, it } from "vitest";
import type { ApiEvent } from "./event-from-api";
import { eventFromApi } from "./event-from-api";

const complete: ApiEvent = {
  id: "colon-el-cascanueces-20261118T2000",
  category: "theatre",
  title: "El Cascanueces",
  artist: "Ballet Estable",
  venue: "Teatro Colón",
  city: "Buenos Aires",
  region: "AR-C",
  country: "AR",
  starts_at: "2026-11-14T22:00:00-03:00",
  ticket_links: [{ vendor: "Entradas BA", url: "https://entradas.example/1" }],
  source_url: "https://teatrocolon.org.ar/x",
  image_url: "/media/abc.webp",
  image_origin: "licensed",
  image_author: "Ana",
  image_license: "CC BY 4.0",
  image_source_url: "https://commons.wikimedia.org/wiki/File:X.jpg",
  updated_at: "2026-11-09T12:00:00Z",
  first_seen_at: "2026-11-02T12:00:00Z",
};

describe("eventFromApi", () => {
  it("renames every field and reads the times as dates", () => {
    expect(eventFromApi(complete)).toEqual({
      id: "colon-el-cascanueces-20261118T2000",
      category: "theatre",
      title: "El Cascanueces",
      artist: "Ballet Estable",
      venue: "Teatro Colón",
      city: "Buenos Aires",
      region: "AR-C",
      country: "AR",
      startsAt: new Date("2026-11-15T01:00:00Z"),
      ticketLinks: [{ vendor: "Entradas BA", url: "https://entradas.example/1" }],
      sourceUrl: "https://teatrocolon.org.ar/x",
      imageUrl: "/media/abc.webp",
      imageOrigin: "licensed",
      imageAuthor: "Ana",
      imageLicense: "CC BY 4.0",
      imageSourceUrl: "https://commons.wikimedia.org/wiki/File:X.jpg",
      updatedAt: new Date("2026-11-09T12:00:00Z"),
      firstSeenAt: new Date("2026-11-02T12:00:00Z"),
    });
  });

  it("keeps a Buenos Aires start time as the same instant", () => {
    // Saturday 22:00 in Buenos Aires is Sunday 01:00 UTC.
    expect(eventFromApi(complete).startsAt.toISOString()).toBe("2026-11-15T01:00:00.000Z");
  });

  it("keeps missing facts as null", () => {
    const bare: ApiEvent = {
      ...complete,
      artist: null,
      city: null,
      region: null,
      country: null,
      image_url: null,
      image_origin: null,
      image_author: null,
      image_license: null,
      image_source_url: null,
    };
    const event = eventFromApi(bare);
    expect([event.artist, event.city, event.region, event.country]).toEqual([null, null, null, null]);
    expect([event.imageUrl, event.imageOrigin, event.imageAuthor, event.imageLicense, event.imageSourceUrl]).toEqual([
      null,
      null,
      null,
      null,
      null,
    ]);
  });
});
