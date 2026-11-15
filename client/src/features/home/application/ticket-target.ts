import type { Show } from "../../events/domain/show";

/** The ticket page of a show's next date, and which date and ticketer it is (what a click is counted for). */
export type TicketTarget = { url: string; domain: string; eventId: string; vendor: string | null };

/** Where in the app a ticket click came from; the API counts it per place. */
export type ClickSource = "show" | "spotlight";

// A regex instead of URL: React Native's URL does not implement hostname.
const HOST = /^[a-z][a-z0-9+.-]*:\/\/(?:www\.)?([^/:?#]+)/i;

/** Where the ticket button goes: the next date's first ticket link, else the show's source page. */
export function ticketTarget(show: Show): TicketTarget {
  const date = show.dates[0];
  const link = date.ticketLinks[0];
  const url = link?.url ?? show.sourceUrl;
  return { url, domain: domainOf(url), eventId: date.id, vendor: link?.vendor ?? null };
}

/**
 * What a ticket button opens: the API's /go address for that date, which counts the click and sends the
 * visitor on to the ticket page (with our utm_source). The ticketer is left out when the date has no link.
 */
export function trackedTicketUrl(apiBase: string, eventId: string, vendor: string | null, from: ClickSource): string {
  const query = [vendor ? `v=${encodeURIComponent(vendor)}` : null, `from=${from}`].filter(Boolean).join("&");
  return `${apiBase.replace(/\/+$/, "")}/go/${encodeURIComponent(eventId)}?${query}`;
}

/** "movistararena.com.ar" from a link: the host without "www.", or the link itself when it has none. */
export function domainOf(url: string): string {
  return HOST.exec(url)?.[1] ?? url;
}
