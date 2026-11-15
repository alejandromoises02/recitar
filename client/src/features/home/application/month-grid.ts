import { addDays, dayFromIso, mondayOf } from "./calendar";
import { DATE_WORDS } from "./date-words";
import type { Lang } from "../../../i18n/lang";

export type MonthCell = { iso: string; day: number; inMonth: boolean; disabled: boolean; today: boolean };

/** "2026-11" moved by `months` months. */
export function shiftMonth(month: string, months: number): string {
  const [year, index] = month.split("-").map(Number);
  return new Date(Date.UTC(year, index - 1 + months, 1)).toISOString().slice(0, 7);
}

export function monthTitle(month: string, lang: Lang): string {
  const [year, index] = month.split("-").map(Number);
  return DATE_WORDS[lang].monthTitle(index, year);
}

/** The weeks (Monday to Sunday) that cover `month`; days before `today` cannot be picked. */
export function monthGrid(month: string, today: string): MonthCell[][] {
  const first = `${month}-01`;
  const last = addDays(`${shiftMonth(month, 1)}-01`, -1);
  const weeks: MonthCell[][] = [];
  for (let start = mondayOf(first); start <= last; start = addDays(start, 7)) {
    weeks.push(
      Array.from({ length: 7 }, (_, i) => {
        const iso = addDays(start, i);
        return { iso, day: dayFromIso(iso).day, inMonth: iso.startsWith(month), disabled: iso < today, today: iso === today };
      }),
    );
  }
  return weeks;
}
