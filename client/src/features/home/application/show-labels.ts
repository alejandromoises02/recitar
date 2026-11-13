/** Labels for the home's show cards. All dates are Buenos Aires calendar days. */

import { MONTHS, WEEKDAYS_SHORT, calendarDay } from "./calendar";

const pad2 = (n: number) => String(n).padStart(2, "0");
const dayNumber = (date: Date) => {
  const { year, month, day } = calendarDay(date);
  return Date.UTC(year, month - 1, day) / 86_400_000;
};

export function daysUntilLabel(startsAt: Date, now: Date): string {
  const days = dayNumber(startsAt) - dayNumber(now);
  if (days <= 0) return "Hoy";
  if (days === 1) return "Mañana";
  if (days === 2) return "Pasado mañana";
  return `En ${days} días`;
}

/** Day and short month name. */
export function shortDate(startsAt: Date): string {
  const { month, day } = calendarDay(startsAt);
  return `${day} ${MONTHS[month - 1].slice(0, 3)}`;
}

/** Weekday and DD/MM, plus a two-digit year when not this year: shows get announced a year ahead. */
export function boardDate(startsAt: Date, now: Date): string {
  const { year, month, day, weekday } = calendarDay(startsAt);
  const yearSuffix = year === calendarDay(now).year ? "" : `/${pad2(year % 100)}`;
  return `${WEEKDAYS_SHORT[weekday]} ${pad2(day)}/${pad2(month)}${yearSuffix}`;
}

/** Weekday and DD/MM/YYYY. */
export function longDate(startsAt: Date): string {
  const { year, month, day, weekday } = calendarDay(startsAt);
  return `${WEEKDAYS_SHORT[weekday]} ${pad2(day)}/${pad2(month)}/${year}`;
}

/** How many dates follow the first one; empty for a single date. */
export function moreDatesLabel(dateCount: number): string {
  const more = dateCount - 1;
  if (more <= 0) return "";
  return `+${more} ${more === 1 ? "fecha" : "fechas"}`;
}

const ALNUM = /[\p{L}\p{N}]/u;

/** Two characters for a show without a photo; "?" when the name has no letters or digits. */
export function initials(name: string): string {
  const words = name.split(/\s+/).filter((word) => ALNUM.test(word));
  const chars =
    words.length >= 2
      ? words.slice(0, 2).map((word) => word.match(ALNUM)![0])
      : [...(words[0] ?? "")].filter((c) => ALNUM.test(c)).slice(0, 2);
  return chars.length ? chars.join("").toLocaleUpperCase("es") : "?";
}

/** Our own image copies come as API-relative "/media/..." paths. */
export function imageSource(imageUrl: string | null, apiBase: string): string | null {
  if (!imageUrl) return null;
  if (/^https?:\/\//.test(imageUrl)) return imageUrl;
  return `${apiBase.replace(/\/+$/, "")}${imageUrl.startsWith("/") ? "" : "/"}${imageUrl}`;
}
