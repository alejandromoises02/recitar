import type { Page } from "@playwright/test";

/** A fixed "now" for every test: Saturday 14 November 2026, 12:00 in Buenos Aires. */
export const NOW = new Date("2026-11-14T15:00:00Z");

const day = (days: number, hour = 21) => new Date(NOW.getTime() + days * 86_400_000 + (hour - 12) * 3_600_000).toISOString();

/** `pagePerDate`: each date has its own ticket page (most ticketers share one page per show). */
function show(id: string, name: string, venue: string, inDays: number[], pagePerDate = false, extra: Record<string, unknown> = {}) {
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
    spotify_artist_id: null,
    ...extra,
  };
}

/** A venue's wide banner (900x300, like Teatro Gran Rivadavia's), served by the fake API host. */
export const BANNER_URL = "http://a11y-api.test/media/banner.svg";
const BANNER_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="300" viewBox="0 0 900 300"><rect width="900" height="300" fill="#333"/></svg>';

const SHOWS = [
  show("s1", "Jazz Quartet", "Centro Cultural Nueva Uriarte", [0], false, { artist: "Jazz Quartet", spotify_artist_id: "0jazzquartet00000000000" }),
  show("s2", "La tempestad", "Teatro Colón", [1, 8], true),
  show("s3", "Club 69", "Niceto Club", [1]),
  show("s4", "Die Walküre", "Teatro Colón", [3, 5, 7]),
  show("s5", "María Becerra", "Movistar Arena", [17]),
  show("s6", "Giant Rooks", "Teatro Vorterix", [18], false, { image_url: BANNER_URL, image_origin: "source" }),
];

const json = (body: unknown) => ({ status: 200, contentType: "application/json", headers: { "access-control-allow-origin": "*" }, body: JSON.stringify(body) });

/**
 * Freezes the clock and answers the API the home calls with fixed shows. Also does what the web host
 * must do in production: serve the one pre-rendered show/[id].html for any /show/<id> (static output
 * renders that template once; without the rewrite a shared show link is a 404).
 */
export async function withFakeApi(page: Page) {
  await page.clock.setFixedTime(NOW);
  // Spotify stands in locally, so the tests never depend on the network: the embed is a page with a play
  // button, and the iFrame API replaces its element with that page, as the real one does.
  await page.route(
    (url) => url.hostname === "open.spotify.com",
    (route) => {
      const { pathname } = new URL(route.request().url());
      if (pathname.startsWith("/embed/iframe-api")) {
        return route.fulfill({
          contentType: "text/javascript",
          body: `window.onSpotifyIframeApiReady({ createController(element, options, ready) {
            const frame = document.createElement("iframe");
            frame.src = "https://open.spotify.com/embed/artist/" + options.uri.split(":").pop();
            frame.title = "Spotify Embed";
            element.replaceWith(frame);
            ready({ togglePlay() {}, destroy() { frame.remove(); }, addListener() {} });
          } });`,
        });
      }
      return route.fulfill({ contentType: "text/html", body: '<!doctype html><html lang="en"><title>Spotify Embed</title><button>Play</button></html>' });
    },
  );
  await page.route(
    (url) => url.hostname === "localhost" && /^\/show\/[^/.]+$/.test(url.pathname),
    (route) => route.fulfill({ path: "dist/show/[id].html", contentType: "text/html" }),
  );
  await page.route(
    (url) => url.hostname === "a11y-api.test",
    (route) => {
      const { pathname, searchParams } = new URL(route.request().url());
      if (pathname.endsWith("/media/banner.svg")) return route.fulfill({ contentType: "image/svg+xml", headers: { "access-control-allow-origin": "*" }, body: BANNER_SVG });
      if (pathname.endsWith("/track")) {
        const cors = { "access-control-allow-origin": "*", "access-control-allow-methods": "GET, POST", "access-control-allow-headers": "Content-Type" };
        return route.fulfill({ status: 204, headers: cors });
      }
      if (pathname.endsWith("/featured")) return route.fulfill(json({ kind: "picked", items: SHOWS.slice(0, 3) }));
      if (pathname.endsWith("/venues")) return route.fulfill(json({ items: [...new Set(SHOWS.map((s) => s.venue))].map((name) => ({ name, upcoming_events: 1 })) }));
      if (pathname.endsWith("/shows")) {
        const venues = searchParams.getAll("venue");
        return route.fulfill(json({ items: venues.length > 0 ? SHOWS.filter((show) => venues.includes(show.venue)) : SHOWS, next_cursor: null }));
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
