import type { Page } from "@playwright/test";

/** A fixed "now" for every test: Saturday 14 November 2026, 12:00 in Buenos Aires. */
export const NOW = new Date("2026-11-14T15:00:00Z");

const day = (days: number, hour = 21) => new Date(NOW.getTime() + days * 86_400_000 + (hour - 12) * 3_600_000).toISOString();

function show(id: string, name: string, venue: string, inDays: number[]) {
  return {
    id,
    category: "concert",
    title: name,
    name,
    artist: null,
    venue,
    city: "Buenos Aires",
    region: null,
    country: "AR",
    source_url: `https://tickets.example/${id}`,
    image_url: null,
    image_origin: null,
    image_author: null,
    image_license: null,
    image_source_url: null,
    first_seen_at: day(-1, 10),
    dates: inDays.map((d, i) => ({ id: `${id}-${i}`, starts_at: day(d), ticket_links: [{ vendor: "Ticketek", url: `https://tickets.example/${id}` }] })),
  };
}

const SHOWS = [
  show("s1", "Jazz Quartet", "Centro Cultural Nueva Uriarte", [0]),
  show("s2", "La tempestad", "Teatro Colón", [1, 8]),
  show("s3", "Club 69", "Niceto Club", [1]),
  show("s4", "Die Walküre", "Teatro Colón", [3, 5, 7]),
  show("s5", "María Becerra", "Movistar Arena", [17]),
  show("s6", "Giant Rooks", "Teatro Vorterix", [18]),
];

const json = (body: unknown) => ({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) });

/** Freezes the clock and answers the API the home calls with fixed shows. */
export async function withFakeApi(page: Page) {
  await page.clock.setFixedTime(NOW);
  await page.route(
    (url) => url.hostname === "a11y-api.test",
    (route) => {
      const { pathname } = new URL(route.request().url());
      if (pathname.endsWith("/featured")) return route.fulfill(json({ kind: "picked", items: SHOWS.slice(0, 3) }));
      if (pathname.endsWith("/venues")) return route.fulfill(json({ items: [...new Set(SHOWS.map((s) => s.venue))].map((name) => ({ name, upcoming_events: 1 })) }));
      if (pathname.endsWith("/shows")) return route.fulfill(json({ items: SHOWS, next_cursor: null }));
      return route.fulfill({ status: 404, headers: { "access-control-allow-origin": "*" } });
    },
  );
}
