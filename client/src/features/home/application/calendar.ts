/** Buenos Aires calendar days as "YYYY-MM-DD" strings, so comparisons and maths stay plain. */

const BUENOS_AIRES = "America/Argentina/Buenos_Aires";
const DAY = new Intl.DateTimeFormat("en-CA", { timeZone: BUENOS_AIRES, year: "numeric", month: "2-digit", day: "2-digit" });
const TIME = new Intl.DateTimeFormat("en-GB", { timeZone: BUENOS_AIRES, hour: "2-digit", minute: "2-digit", hourCycle: "h23" });


export type CalendarDay = { iso: string; year: number; month: number; day: number; weekday: number };

const parts = (iso: string): CalendarDay => {
  const [year, month, day] = iso.split("-").map(Number);
  return { iso, year, month, day, weekday: new Date(Date.UTC(year, month - 1, day)).getUTCDay() };
};

/** The Buenos Aires calendar day `date` falls on. */
export const calendarDay = (date: Date): CalendarDay => parts(DAY.format(date));

export const dayFromIso = parts;

export function addDays(iso: string, days: number): string {
  const { year, month, day } = parts(iso);
  return new Date(Date.UTC(year, month - 1, day + days)).toISOString().slice(0, 10);
}

/** Monday of the week `iso` is in. */
export const mondayOf = (iso: string) => addDays(iso, -((parts(iso).weekday + 6) % 7));

export function lastDayOfMonth(iso: string): string {
  const { year, month } = parts(iso);
  return new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
}

/** "21:30" in Buenos Aires time. */
export const clockTime = (date: Date) => TIME.format(date);
