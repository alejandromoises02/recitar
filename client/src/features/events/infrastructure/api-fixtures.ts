/** Test data shaped like the API's JSON (shared by several test files). */
import type { ApiShow } from "./event-from-api";

export const apiShow = (id: string, dates = ["2026-11-14T22:00:00-03:00"]): ApiShow => ({
  id,
  category: "concert",
  title: `${id.toUpperCase()} en Niceto Bar`,
  name: `Show ${id}`,
  artist: "Artista",
  venue: "Niceto Club",
  city: "Buenos Aires",
  region: "AR-C",
  country: "AR",
  source_url: `https://venti.live/${id}`,
  image_url: "/media/x.webp",
  image_origin: "licensed",
  image_author: "Ana",
  image_license: "CC BY 4.0",
  image_source_url: "https://commons.wikimedia.org/wiki/File:X.jpg",
  first_seen_at: "2026-11-02T12:00:00Z",
  updated_at: "2026-11-13T12:00:00Z",
  dates: dates.map((startsAt, i) => ({
    id: `${id}-${i}`,
    starts_at: startsAt,
    time_known: true,
    ticket_links: [{ vendor: "Venti", url: `https://venti.live/${id}/${i}` }],
  })),
});
