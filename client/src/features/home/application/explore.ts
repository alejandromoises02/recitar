import type { Show } from "../../events/domain/show";
import { addDays, calendarDay, dayFromIso, lastDayOfMonth, mondayOf } from "./calendar";
import { DATE_WORDS } from "./date-words";
import { startTime } from "./show-labels";
import type { Lang } from "../../../i18n/lang";
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
export function stripDays(now: Date, lang: Lang): StripDay[] {
  const words = DATE_WORDS[lang];
  const today = calendarDay(now).iso;
  return Array.from({ length: EXPLORE_DAYS }, (_, i) => {
    const day = dayFromIso(addDays(today, i));
    return { iso: day.iso, label: i === 0 ? words.todayShort : words.weekdaysShort[day.weekday], day: day.day };
  });
}

export type PickedDayTile = StripDay & { month: string };

/** A day picked in the calendar: weekday, day and short month, plus a two-digit year when not this year. */
export function pickedDayTile(iso: string, now: Date, lang: Lang): PickedDayTile {
  const words = DATE_WORDS[lang];
  const day = dayFromIso(iso);
  const year = day.year === calendarDay(now).year ? "" : ` ${String(day.year % 100).padStart(2, "0")}`;
  return { iso, label: words.weekdaysShort[day.weekday], day: day.day, month: `${words.monthsShort[day.month - 1]}${year}` };
}

export function daysWithShows(shows: Show[]): Set<string> {
  return new Set(shows.flatMap((show) => show.dates.map((date) => calendarDay(date.startsAt).iso)));
}

export type ShowItem = { key: string; show: Show; date: Date; timeKnown: boolean };
export type DayBlock = { iso: string; weekday: string; day: number; month: string; note: string | null; items: ShowItem[] };
export type ShowGroup = { key: string; title: string; note: string | null; count: number; days: DayBlock[] };

function dayNote(iso: string, today: string, lang: Lang): string | null {
  if (iso === today) return DATE_WORDS[lang].today;
  return iso === addDays(today, 1) ? DATE_WORDS[lang].tomorrow : null;
}

function groupHead(iso: string, by: GroupBy, today: string, lang: Lang) {
  const words = DATE_WORDS[lang];
  const day = dayFromIso(iso);
  if (by === "day") return { key: iso, title: words.dayTitle(day.weekday, day.day, day.month), note: dayNote(iso, today, lang) };
  if (by === "week") {
    const monday = dayFromIso(mondayOf(iso));
    const sunday = dayFromIso(addDays(monday.iso, 6));
    const note = monday.iso === mondayOf(today) ? words.thisWeek : null;
    return { key: monday.iso, title: words.weekTitle(monday, sunday), note };
  }
  return { key: iso.slice(0, 7), title: words.monthTitle(day.month, day.year), note: null };
}

function dayBlock(iso: string, today: string, lang: Lang): DayBlock {
  const words = DATE_WORDS[lang];
  const day = dayFromIso(iso);
  return { iso, weekday: words.weekdaysShort[day.weekday], day: day.day, month: words.monthsShort[day.month - 1], note: dayNote(iso, today, lang), items: [] };
}

const inRange = (iso: string, range: DayRange) => (!range.from || iso >= range.from) && (!range.to || iso <= range.to);

/**
 * Every date of every show inside `range`, by month, week or day, and inside each group one block
 * per day, in date order. Dates after `horizon` are left out: shows not loaded yet may still have
 * dates before them (the API pages shows by their next date).
 */
export function groupShows(shows: Show[], by: GroupBy, now: Date, lang: Lang, range: DayRange, horizon: Date | null = null): ShowGroup[] {
  const today = calendarDay(now).iso;
  const items = shows
    .flatMap((show) =>
      show.dates
        .filter(({ startsAt }) => inRange(calendarDay(startsAt).iso, range) && (!horizon || startsAt <= horizon))
        .map(({ id, startsAt, timeKnown }) => ({ key: id, show, date: startsAt, timeKnown })),
    )
    .sort((a, b) => a.date.getTime() - b.date.getTime());
  const groups = new Map<string, ShowGroup>();
  for (const item of items) {
    const iso = calendarDay(item.date).iso;
    const head = groupHead(iso, by, today, lang);
    const group = groups.get(head.key) ?? { ...head, count: 0, days: [] };
    let block = group.days.at(-1);
    if (block?.iso !== iso) {
      block = dayBlock(iso, today, lang);
      group.days.push(block);
    }
    block.items.push(item);
    group.count += 1;
    groups.set(head.key, group);
  }
  return [...groups.values()];
}

export function cardDate(date: Date, lang: Lang) {
  const words = DATE_WORDS[lang];
  const day = calendarDay(date);
  return { weekday: words.weekdaysShort[day.weekday], day: day.day, month: words.monthsShort[day.month - 1] };
}

export const timeLabel = (date: Date, timeKnown: boolean, lang: Lang) => startTime(date, timeKnown, lang);

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

/** How many filters narrow the listing: search, venue and date ("Ver por" only arranges it). */
export function activeFilterCount(filters: { text: string; venues: string[]; when: When }): number {
  return [filters.text.trim() !== "", filters.venues.length > 0, filters.when !== "all"].filter(Boolean).length;
}

export type ListingStatus = { kind: "error" } | { kind: "empty" } | { kind: "count"; count: number; more: boolean };

/** What the listing says to screen readers once it settles; null while there is nothing settled to say. */
export function listingStatus(state: {
  isPending: boolean;
  isError: boolean;
  loaded: boolean;
  visible: number;
  count: number;
  hasNextPage: boolean;
}): ListingStatus | null {
  if (state.isError) return { kind: "error" };
  if (state.isPending || !state.loaded) return null;
  if (state.visible === 0) return state.hasNextPage ? null : { kind: "empty" };
  return { kind: "count", count: state.count, more: state.hasNextPage };
}
