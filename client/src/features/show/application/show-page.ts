import type { Lang } from "../../../i18n/lang";
import type { Show, ShowDateTickets, ShowDetail } from "../../events/domain/show";
import { calendarDay } from "../../home/application/calendar";
import { DATE_WORDS } from "../../home/application/date-words";
import { startTime } from "../../home/application/show-labels";
import { VENUE_TO_BE_CONFIRMED } from "../../events/domain/venue";
import { domainOf } from "../../home/application/ticket-target";

const pad2 = (n: number) => String(n).padStart(2, "0");
const capitalise = (text: string) => text.charAt(0) + text.slice(1).toLowerCase();

export type DateTile = { weekday: string; day: string; month: string; time: string };

/** A date tile: weekday, day, short month (plus a two-digit year when not this year) and time, in Buenos Aires. */
export function dateTile(startsAt: Date, now: Date, lang: Lang, timeKnown = true): DateTile {
  const words = DATE_WORDS[lang];
  const day = calendarDay(startsAt);
  const year = day.year === calendarDay(now).year ? "" : ` ${pad2(day.year % 100)}`;
  return { weekday: words.weekdaysShort[day.weekday], day: pad2(day.day), month: `${words.monthsShort[day.month - 1]}${year}`, time: startTime(startsAt, timeKnown, lang, "short") };
}

/** The picked date under the ticket button: "Mié 18/11 · 21:00", with "/27" when not this year and "Hora a confirmar" for an unknown time. */
export function buttonWhen(startsAt: Date, now: Date, lang: Lang, timeKnown = true): string {
  const day = calendarDay(startsAt);
  const year = day.year === calendarDay(now).year ? "" : `/${pad2(day.year % 100)}`;
  return `${capitalise(DATE_WORDS[lang].weekdaysShort[day.weekday])} ${pad2(day.day)}/${pad2(day.month)}${year} · ${startTime(startsAt, timeKnown, lang)}`;
}

export type TicketTarget = { vendor: string | null; url: string; domain: string };

/** Where a date's tickets are: one target per vendor, or the source page when the date has no link. */
export function dateTargets(date: ShowDateTickets, sourceUrl: string): TicketTarget[] {
  if (date.ticketLinks.length === 0) return [{ vendor: null, url: sourceUrl, domain: domainOf(sourceUrl) }];
  return date.ticketLinks.map(({ vendor, url }) => ({ vendor, url, domain: domainOf(url) }));
}

/**
 * How the page offers the dates. Most ticketers have one page per show and pick the date there, so
 * when every date shares its ticket page (or has none yet) the dates are only listed: picking one here
 * would promise a date the ticket page would not open. Only dates with pages of their own are picked.
 */
export type DateMode = "single" | "list" | "pick";

export function dateMode(dates: ShowDateTickets[]): DateMode {
  if (dates.length === 1) return "single";
  const pages = new Set(dates.flatMap((date) => date.ticketLinks.map((link) => link.url)));
  return pages.size > 1 ? "pick" : "list";
}

/** `eventId` is the date a click on the button is counted for. */
export type TicketPlan =
  | { kind: "date"; eventId: string; targets: TicketTarget[] }
  | { kind: "any-date"; eventId: string; targets: TicketTarget[] }
  | { kind: "not-on-sale"; eventId: string; source: { url: string; domain: string } };

/** What the ticket button does: buy the picked date, choose the date on the ticketer's site, or not on sale yet. */
export function ticketPlan(dates: ShowDateTickets[], picked: number, sourceUrl: string): TicketPlan {
  const notOnSale = (eventId: string): TicketPlan => ({ kind: "not-on-sale", eventId, source: { url: sourceUrl, domain: domainOf(sourceUrl) } });
  if (dateMode(dates) === "list") {
    const onSale = dates.find((date) => date.ticketLinks.length > 0);
    return onSale ? { kind: "any-date", eventId: onSale.id, targets: dateTargets(onSale, sourceUrl) } : notOnSale(dates[0].id);
  }
  const date = dates[Math.min(picked, dates.length - 1)];
  return date.ticketLinks.length > 0 ? { kind: "date", eventId: date.id, targets: dateTargets(date, sourceUrl) } : notOnSale(date.id);
}

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "actualizado hace 21 h" / "updated 21 h ago": how old the data on the page is. */
export function updatedAgo(updatedAt: Date, now: Date, lang: Lang): string {
  const elapsed = Math.max(0, now.getTime() - updatedAt.getTime());
  const days = Math.floor(elapsed / DAY);
  const hours = Math.floor(elapsed / HOUR);
  const minutes = Math.floor(elapsed / MINUTE);
  if (lang === "en") {
    if (minutes < 5) return "updated just now";
    if (hours < 1) return `updated ${minutes} min ago`;
    if (days < 1) return `updated ${hours} h ago`;
    return `updated ${days} ${days === 1 ? "day" : "days"} ago`;
  }
  if (minutes < 5) return "actualizado recién";
  if (hours < 1) return `actualizado hace ${minutes} min`;
  if (days < 1) return `actualizado hace ${hours} h`;
  return `actualizado hace ${days} ${days === 1 ? "día" : "días"}`;
}

/** Whether the page offers other shows at the venue: a venue still to be confirmed is not a place. */
export function hasVenueToExplore(venue: string): boolean {
  return venue !== VENUE_TO_BE_CONFIRMED;
}

/** How many other shows the page offers at the same venue. */
export const MORE_AT_VENUE = 4;

/** Up to MORE_AT_VENUE shows at the venue, soonest first as the API sends them, never the page's own show. */
export function moreAtVenue(shows: Show[], currentId: string): Show[] {
  return shows.filter((show) => show.id !== currentId).slice(0, MORE_AT_VENUE);
}

/** What the venue map searches for: venue, street address and city, leaving out what is unknown. Searching by
 * name also places venues we have no coordinates for. null while the venue is to be confirmed. */
export function venueMapQuery(show: Pick<ShowDetail, "venue" | "city" | "venueLocation">): string | null {
  if (!hasVenueToExplore(show.venue)) return null;
  return [show.venue, show.venueLocation?.address, show.city].filter(Boolean).join(", ");
}

/** Google's embeddable map for a search, in the app language. Keyless: the form Google Maps' own share link uses. */
export function mapEmbedUrl(query: string, lang: Lang): string {
  return `https://maps.google.com/maps?q=${encodeURIComponent(query)}&z=16&hl=${lang}&output=embed`;
}

/** Spotify's embeddable artist player: it plays the artist's top tracks; Spotify decides when a listener gets only a preview. */
export function spotifyEmbedUrl(artistId: string): string {
  return `https://open.spotify.com/embed/artist/${encodeURIComponent(artistId)}`;
}

/** Spotify's iFrame API: the embed with play and pause the page can call (developer.spotify.com/documentation/embeds). */
export const SPOTIFY_IFRAME_API = "https://open.spotify.com/embed/iframe-api/v1";

export function spotifyArtistUri(artistId: string): string {
  return `spotify:artist:${artistId}`;
}

/** A JSON string literal that is also safe inside an inline <script> ("</script>" cannot close it). */
const scriptString = (text: string) => JSON.stringify(text).replace(/</g, "\\u003c");

/**
 * The app's page for a Spotify sample: the iFrame API's player for `uri`, `height` tall. It posts
 * `{"playing": boolean}` to the app on every playback change; the app toggles it by running
 * `window.player.togglePlay()`.
 */
export function spotifySamplePage(uri: string, height: number): string {
  return (
    '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>' +
    '<body style="margin:0;background:transparent"><div id="embed"></div><script>' +
    "window.onSpotifyIframeApiReady = function (api) {" +
    `api.createController(document.getElementById("embed"), { uri: ${scriptString(uri)}, width: "100%", height: ${Number(height)} }, function (player) {` +
    "window.player = player;" +
    'player.addListener("playback_update", function (event) { window.ReactNativeWebView.postMessage(JSON.stringify({ playing: !event.data.isPaused })); });' +
    "});};" +
    `</script><script src="${SPOTIFY_IFRAME_API}" async></script></body></html>`
  );
}

/** A photo at least this many times wider than tall is a banner (a venue's 900x300), not a poster. */
export const WIDE_BANNER_RATIO = 2;

/** A banner shown in the poster's frame beside the info would be a thin strip; it goes under the title instead. */
export function isWideBanner(ratio: number | null): boolean {
  return ratio !== null && ratio >= WIDE_BANNER_RATIO;
}

const escapeAttribute = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

/** A page holding only the map, for the app's WebView: Google answers "must be used in an iframe" to a top-level load. */
export function mapEmbedPage(url: string): string {
  return (
    '<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>' +
    '<body style="margin:0;background:#E9E5DC">' +
    `<iframe src="${escapeAttribute(url)}" style="border:0;width:100%;height:100vh;display:block"></iframe>` +
    "</body></html>"
  );
}
