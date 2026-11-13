import type { Show } from "../../events/domain/show";

export type TicketTarget = { url: string; domain: string };

// A regex instead of URL: React Native's URL does not implement hostname.
const HOST = /^[a-z][a-z0-9+.-]*:\/\/(?:www\.)?([^/:?#]+)/i;

/** Where the ticket button goes: the next date's first ticket link, else the show's source page. */
export function ticketTarget(show: Show): TicketTarget {
  const url = show.dates[0]?.ticketLinks[0]?.url ?? show.sourceUrl;
  return { url, domain: HOST.exec(url)?.[1] ?? url };
}
