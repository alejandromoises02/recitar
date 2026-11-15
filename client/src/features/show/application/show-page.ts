import type { Lang } from "../../../i18n/lang";
import type { ShowDateTickets } from "../../events/domain/show";
import { calendarDay, clockTime } from "../../home/application/calendar";
import { DATE_WORDS } from "../../home/application/date-words";
import { domainOf } from "../../home/application/ticket-target";

const pad2 = (n: number) => String(n).padStart(2, "0");
const capitalise = (text: string) => text.charAt(0) + text.slice(1).toLowerCase();

export type DateTile = { weekday: string; day: string; month: string; time: string };

/** A date tile: weekday, day, short month (plus a two-digit year when not this year) and time, in Buenos Aires. */
export function dateTile(startsAt: Date, now: Date, lang: Lang): DateTile {
  const words = DATE_WORDS[lang];
  const day = calendarDay(startsAt);
  const year = day.year === calendarDay(now).year ? "" : ` ${pad2(day.year % 100)}`;
  return { weekday: words.weekdaysShort[day.weekday], day: pad2(day.day), month: `${words.monthsShort[day.month - 1]}${year}`, time: clockTime(startsAt) };
}

/** The picked date under the ticket button: "Mié 18/11 · 21:00", with "/27" when not this year. */
export function buttonWhen(startsAt: Date, now: Date, lang: Lang): string {
  const day = calendarDay(startsAt);
  const year = day.year === calendarDay(now).year ? "" : `/${pad2(day.year % 100)}`;
  return `${capitalise(DATE_WORDS[lang].weekdaysShort[day.weekday])} ${pad2(day.day)}/${pad2(day.month)}${year} · ${clockTime(startsAt)}`;
}

export type TicketTarget = { vendor: string | null; url: string; domain: string };

/** Where a date's tickets are: one target per vendor, or the source page when the date has no link. */
export function dateTargets(date: ShowDateTickets, sourceUrl: string): TicketTarget[] {
  if (date.ticketLinks.length === 0) return [{ vendor: null, url: sourceUrl, domain: domainOf(sourceUrl) }];
  return date.ticketLinks.map(({ vendor, url }) => ({ vendor, url, domain: domainOf(url) }));
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
