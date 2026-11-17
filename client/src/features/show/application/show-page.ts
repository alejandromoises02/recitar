import type { Lang } from "../../../i18n/lang";
import type { Show, ShowDateTickets } from "../../events/domain/show";
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
