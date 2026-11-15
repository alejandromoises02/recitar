import type { Show } from "../../events/domain/show";
import { MONTHS, WEEKDAYS, WEEKDAYS_SHORT, addDays, calendarDay, clockTime, dayFromIso, lastDayOfMonth, mondayOf } from "./calendar";
import { EXPLORE_DAYS } from "./explore.constants";

export type When = "all" | "today" | "weekend" | "week" | "month" | "day";
export type GroupBy = "month" | "week" | "day";
export type DayRange = { from?: string; to?: string };

export function whenRange(when: When, now: Date, pickedDay?: string): DayRange {
  const today = calendarDay(now).iso;
  const monday = mondayOf(today);
  const sunday = addDays(monday, 6);
  switch (when) {
    case "today":
      return { from: today, to: today };
    case "weekend": {
      const friday = addDays(monday, 4);
      return { from: friday < today ? today : friday, to: sunday };
    }
    case "week":
      return { from: today, to: sunday };
    case "month":
      return { from: today, to: lastDayOfMonth(today) };
    case "day":
      return pickedDay ? { from: pickedDay, to: pickedDay } : {};
    default:
      return {};
  }
}

export type StripDay = { iso: string; label: string; day: number };

/** Today and the days right after it, for the quick day picker. */
export function stripDays(now: Date): StripDay[] {
  const today = calendarDay(now).iso;
  return Array.from({ length: EXPLORE_DAYS }, (_, i) => {
    const day = dayFromIso(addDays(today, i));
    return { iso: day.iso, label: i === 0 ? "HOY" : WEEKDAYS_SHORT[day.weekday], day: day.day };
  });
}

export type PickedDayTile = StripDay & { month: string };

/** A day picked in the calendar: weekday, day and short month, plus a two-digit year when not this year. */
export function pickedDayTile(iso: string, now: Date): PickedDayTile {
  const day = dayFromIso(iso);
  const year = day.year === calendarDay(now).year ? "" : ` ${String(day.year % 100).padStart(2, "0")}`;
  return { iso, label: WEEKDAYS_SHORT[day.weekday], day: day.day, month: `${MONTHS_SHORT[day.month - 1]}${year}` };
}

export function daysWithShows(shows: Show[]): Set<string> {
  return new Set(shows.flatMap((show) => show.dates.map((date) => calendarDay(date.startsAt).iso)));
}

const MONTHS_SHORT = MONTHS.map((m) => m.slice(0, 3).toUpperCase());

export type ShowItem = { key: string; show: Show; date: Date };
export type DayBlock = { iso: string; weekday: string; day: number; month: string; note: string | null; items: ShowItem[] };
export type ShowGroup = { key: string; title: string; note: string | null; count: number; days: DayBlock[] };

const capitalise = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

function groupHead(iso: string, by: GroupBy, today: string) {
  if (by === "day") {
    const day = dayFromIso(iso);
    const note = iso === today ? "Hoy" : iso === addDays(today, 1) ? "Mañana" : null;
    return { key: iso, title: `${WEEKDAYS[day.weekday]} ${day.day} de ${MONTHS[day.month - 1]}`, note };
  }
  if (by === "week") {
    const monday = dayFromIso(mondayOf(iso));
    const sunday = dayFromIso(addDays(monday.iso, 6));
    const start = monday.month === sunday.month ? `${monday.day}` : `${monday.day} de ${MONTHS[monday.month - 1]}`;
    const note = monday.iso === mondayOf(today) ? "esta semana" : null;
    return { key: monday.iso, title: `Semana del ${start} al ${sunday.day} de ${MONTHS[sunday.month - 1]}`, note };
  }
  const day = dayFromIso(iso);
  return { key: iso.slice(0, 7), title: `${capitalise(MONTHS[day.month - 1])} ${day.year}`, note: null };
}

function dayBlock(iso: string, today: string): DayBlock {
  const day = dayFromIso(iso);
  const note = iso === today ? "Hoy" : iso === addDays(today, 1) ? "Mañana" : null;
  return { iso, weekday: WEEKDAYS_SHORT[day.weekday], day: day.day, month: MONTHS_SHORT[day.month - 1], note, items: [] };
}

const inRange = (iso: string, range: DayRange) => (!range.from || iso >= range.from) && (!range.to || iso <= range.to);

/**
 * Every date of every show inside `range`, by month, week or day, and inside each group one block
 * per day, in date order. Dates after `horizon` are left out: shows not loaded yet may still have
 * dates before them (the API pages shows by their next date).
 */
export function groupShows(shows: Show[], by: GroupBy, now: Date, range: DayRange, horizon: Date | null = null): ShowGroup[] {
  const today = calendarDay(now).iso;
  const items = shows
    .flatMap((show) =>
      show.dates
        .filter(({ startsAt }) => inRange(calendarDay(startsAt).iso, range) && (!horizon || startsAt <= horizon))
        .map(({ id, startsAt }) => ({ key: id, show, date: startsAt })),
    )
    .sort((a, b) => a.date.getTime() - b.date.getTime());
  const groups = new Map<string, ShowGroup>();
  for (const item of items) {
    const iso = calendarDay(item.date).iso;
    const head = groupHead(iso, by, today);
    const group = groups.get(head.key) ?? { ...head, count: 0, days: [] };
    let block = group.days.at(-1);
    if (block?.iso !== iso) {
      block = dayBlock(iso, today);
      group.days.push(block);
    }
    block.items.push(item);
    group.count += 1;
    groups.set(head.key, group);
  }
  return [...groups.values()];
}

export function cardDate(date: Date) {
  const day = calendarDay(date);
  return { weekday: WEEKDAYS_SHORT[day.weekday], day: day.day, month: MONTHS_SHORT[day.month - 1] };
}

export const timeLabel = clockTime;

export type ExploreRow =
  | { kind: "group"; key: string; group: string; title: string; note: string | null; count: number; expanded: boolean }
  | { kind: "days"; key: string; group: string; blocks: DayBlock[] }
  | { kind: "cards"; key: string; group: string; items: ShowItem[] };

const NONE_COLLAPSED: ReadonlySet<string> = new Set();

function titleRow(group: ShowGroup, expanded: boolean): ExploreRow {
  return { kind: "group", key: `group:${group.key}`, group: group.key, title: group.title, note: group.note, count: group.count, expanded };
}

/**
 * The flat rows a virtualised list renders: each group's title, then its day blocks `columns` per row.
 * Groups in `collapsed` keep only their title.
 */
export function exploreRows(groups: ShowGroup[], columns: number, collapsed = NONE_COLLAPSED): ExploreRow[] {
  return groups.flatMap((group) => {
    const expanded = !collapsed.has(group.key);
    const rows: ExploreRow[] = [titleRow(group, expanded)];
    if (!expanded) return rows;
    for (let i = 0; i < group.days.length; i += columns) {
      const blocks = group.days.slice(i, i + columns);
      rows.push({ kind: "days", key: `days:${group.key}:${blocks[0].iso}`, group: group.key, blocks });
    }
    return rows;
  });
}

/** Wide screens: each group's title, then all its shows as cards, `columns` per row. Groups in `collapsed` keep only their title. */
export function cardRows(groups: ShowGroup[], columns: number, collapsed = NONE_COLLAPSED): ExploreRow[] {
  return groups.flatMap((group) => {
    const expanded = !collapsed.has(group.key);
    const rows: ExploreRow[] = [titleRow(group, expanded)];
    if (!expanded) return rows;
    const items = group.days.flatMap((day) => day.items);
    for (let i = 0; i < items.length; i += columns) {
      const chunk = items.slice(i, i + columns);
      rows.push({ kind: "cards", key: `cards:${group.key}:${i}`, group: group.key, items: chunk });
    }
    return rows;
  });
}
