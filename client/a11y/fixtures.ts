import type { Page } from "@playwright/test";

/** A fixed "now" for every test: Saturday 14 November 2026, 12:00 in Buenos Aires. */
export const NOW = new Date("2026-11-14T15:00:00Z");

const day = (days: number, hour = 21) => new Date(NOW.getTime() + days * 86_400_000 + (hour - 12) * 3_600_000).toISOString();

/** `pagePerDate`: each date has its own ticket page (most ticketers share one page per show). */
function show(id: string, name: string, venue: string, inDays: number[], pagePerDate = false) {
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
    updated_at: day(0, 9),
    dates: inDays.map((d, i) => ({ id: `${id}-${i}`, starts_at: day(d), time_known: true, ticket_links: [{ vendor: "Ticketek", url: pagePerDate ? `https://tickets.example/${id}/${i}` : `https://tickets.example/${id}` }] })),
  };
}

const SHOWS = [
  show("s1", "Jazz Quartet", "Centro Cultural Nueva Uriarte", [0]),
  show("s2", "La tempestad", "Teatro Colón", [1, 8], true),
  show("s3", "Club 69", "Niceto Club", [1]),
  show("s4", "Die Walküre", "Teatro Colón", [3, 5, 7]),
  show("s5", "María Becerra", "Movistar Arena", [17]),
  show("s6", "Giant Rooks", "Teatro Vorterix", [18]),
];

const json = (body: unknown) => ({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) });

/**
 * Freezes the clock and answers the API the home calls with fixed shows. Also does what the web host
 * must do in production: serve the one pre-rendered show/[id].html for any /show/<id> (static output
 * renders that template once; without the rewrite a shared show link is a 404).
 */
export async function withFakeApi(page: Page) {
  await page.clock.setFixedTime(NOW);
  await page.route(
    (url) => url.hostname === "localhost" && /^\/show\/[^/.]+$/.test(url.pathname),
    (route) => route.fulfill({ path: "dist/show/[id].html", contentType: "text/html" }),
  );
  await page.route(
    (url) => url.hostname === "a11y-api.test",
    (route) => {
      const { pathname, searchParams } = new URL(route.request().url());
      if (pathname.endsWith("/featured")) return route.fulfill(json({ kind: "picked", items: SHOWS.slice(0, 3) }));
      if (pathname.endsWith("/venues")) return route.fulfill(json({ items: [...new Set(SHOWS.map((s) => s.venue))].map((name) => ({ name, upcoming_events: 1 })) }));
      if (pathname.endsWith("/shows")) {
        const venue = searchParams.get("venue");
        return route.fulfill(json({ items: venue ? SHOWS.filter((show) => show.venue === venue) : SHOWS, next_cursor: null }));
      }
      const one = /\/shows\/([^/]+)$/.exec(pathname);
      if (one) {
        const found = SHOWS.find((show) => show.id === decodeURIComponent(one[1]));
        if (found) return route.fulfill(json(found));
        return route.fulfill({ status: 404, contentType: "application/problem+json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify({ type: "about:blank", title: "Show not found", status: 404, detail: "x" }) });
      }
      return route.fulfill({ status: 404, headers: { "access-control-allow-origin": "*" } });
    },
  );
}
