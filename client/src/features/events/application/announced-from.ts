/** How many days a show counts as "just announced" (home brief; tune with real data). */
export const JUST_ANNOUNCED_DAYS = 14;

const BUENOS_AIRES_DAY = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Argentina/Buenos_Aires",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

/** The `announced_from` to send: the Buenos Aires day `days` before today, as YYYY-MM-DD. */
export function announcedFrom(now: Date, days: number = JUST_ANNOUNCED_DAYS): string {
  const today = BUENOS_AIRES_DAY.format(now); // en-CA formats as YYYY-MM-DD
  const start = new Date(`${today}T12:00:00Z`); // noon: no day shift when subtracting
  start.setUTCDate(start.getUTCDate() - days);
  return start.toISOString().slice(0, 10);
}
